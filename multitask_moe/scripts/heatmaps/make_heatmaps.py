#!/usr/bin/env python
"""Whole-slide attention heatmaps for the multitask image_only (ABMIL) models.

Self-contained (does not depend on the March explainability script, which expects
the old image_mil checkpoint format). Loads OUR barrett.models.AttentionMIL
checkpoint (state_dict), computes per-tile gated-attention weights, and draws an
overlay on the slide thumbnail + a top-tile grid — matching the existing renderer's
look (red=high attention, blue=low, top tiles outlined).

Selects the top true-positive progressor cases per task from the image_only OOF.
Run in the `pathology` conda env (openslide). CPU only.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageDraw, ImageFont

import openslide

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))
from barrett.models import AttentionMIL  # noqa: E402

BASE = Path("/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/multitask_moe_20260721")
REMAPS = [("/scratchc/", "/mnt/scratche/slow/"), ("/mnt/scratchc/", "/mnt/scratche/slow/")]


def _remap(path: str) -> str:
    for a, b in REMAPS:
        if path.startswith(a):
            return b + path[len(a):]
    return path


def _color(s: float) -> tuple[int, int, int, int]:
    s = float(max(0.0, min(1.0, s)))
    return int(255 * s), 0, int(255 * (1 - s)), 120


def _normalize(raw):
    s = np.nan_to_num(np.asarray(raw, np.float32))
    q1, q99 = float(np.quantile(s, 0.01)), float(np.quantile(s, 0.99))
    if q99 <= q1:
        return np.zeros_like(s)
    return ((np.clip(s, q1, q99) - q1) / (q99 - q1)).astype(np.float32)


def _overlay(slide, coords, scores, level, tile_size, title, out_png):
    thumb = slide.get_thumbnail((2048, 2048)).convert("RGBA")
    w, h = thumb.size
    sw, sh = slide.dimensions
    sx, sy = w / max(sw, 1), h / max(sh, 1)
    ds = float(slide.level_downsamples[int(level)])
    half = 0.5 * float(tile_size) * ds
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov, "RGBA")
    for i in range(len(scores)):
        x, y = float(coords[i, 0]) * ds, float(coords[i, 1]) * ds
        d.rectangle([int((x - half) * sx), int((y - half) * sy),
                     int((x + half) * sx), int((y + half) * sy)], fill=_color(scores[i]))
    comp = Image.alpha_composite(thumb, ov)
    d2 = ImageDraw.Draw(comp, "RGBA")
    for idx in np.argsort(-scores)[:10]:
        x, y = float(coords[idx, 0]) * ds, float(coords[idx, 1]) * ds
        d2.rectangle([int((x - half) * sx), int((y - half) * sy),
                      int((x + half) * sx), int((y + half) * sy)], outline=(0, 0, 0, 220), width=2)
    d2.text((10, 10), title, fill=(255, 255, 255, 255), font=ImageFont.load_default())
    comp.convert("RGB").save(out_png)


def _tile(slide, level, coord, tile_size):
    lw, lh = slide.level_dimensions[int(level)]
    half = tile_size // 2
    x0 = max(0, min(int(coord[0]) - half, lw - tile_size))
    y0 = max(0, min(int(coord[1]) - half, lh - tile_size))
    ds = float(slide.level_downsamples[int(level)])
    return slide.read_region((int(x0 * ds), int(y0 * ds)), int(level), (tile_size, tile_size)).convert("RGB")


def _tile_grid(slide, coords, scores, idxs, level, tile_size, out_png, title):
    ncols = 5
    nrows = int(math.ceil(len(idxs) / ncols))
    cw, ch = tile_size + 6, tile_size + 40
    canvas = Image.new("RGB", (ncols * cw + 6, nrows * ch + 36), (20, 20, 20))
    d = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    d.text((8, 8), title, fill=(255, 255, 255), font=font)
    for j, idx in enumerate(idxs):
        x, y = 6 + (j % ncols) * cw, 34 + (j // ncols) * ch
        canvas.paste(_tile(slide, level, coords[idx], tile_size), (x, y))
        d.rectangle([x, y, x + tile_size, y + tile_size], outline=(255, 255, 255), width=1)
        d.text((x + 2, y + tile_size + 3), "#%d w=%.4f" % (j + 1, scores[idx]), fill=(230, 230, 230), font=font)
    canvas.save(out_png)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True)
    ap.add_argument("--backbone", default="uni2")
    ap.add_argument("--n-cases", type=int, default=4)
    ap.add_argument("--top-tiles", type=int, default=20)
    ap.add_argument("--out-dir", default="")
    args = ap.parse_args()

    output_root = BASE / args.task / "train" / args.backbone
    out_dir = Path(args.out_dir) if args.out_dir else output_root / "heatmaps"
    out_dir.mkdir(parents=True, exist_ok=True)
    index = pd.read_csv(BASE / args.task / "release" / "feature_views" / args.backbone / f"{args.backbone}_index.csv",
                        dtype={"sample_id": str})
    npz_by_sample = dict(zip(index["sample_id"], index["npz_path"]))

    oof = pd.read_csv(output_root / "oof" / "image_only_oof_predictions.csv", dtype={"sample_id": str})
    tp = oof[oof["y_true"] == 1].sort_values("y_prob", ascending=False).head(args.n_cases)
    print(f"{args.task}/{args.backbone}: {len(tp)} true-positive cases selected")

    made = []
    for _, row in tp.iterrows():
        sid = str(row["sample_id"])
        fold = int(row["outer_fold"])
        ckpt = output_root / "image_only" / f"fold{fold}" / "model.pt"
        ck = torch.load(ckpt, map_location="cpu")
        cfg = ck["configuration"]
        npz = np.load(npz_by_sample[sid], allow_pickle=True)
        bag = np.asarray(npz["embeddings"], np.float32)
        coords = np.asarray(npz["coords_level"], np.float32)
        level, tile_size = int(npz["level"]), int(npz["tile_size"])
        slide_path = _remap(str(npz["slide_path"]))
        if not Path(slide_path).exists():
            print(f"  [skip] {sid}: slide missing {slide_path}")
            continue
        model = AttentionMIL(in_dim=bag.shape[1], hidden_dim=int(cfg.get("hidden_dim", 256)),
                             attn_dim=int(cfg.get("attn_dim", 128)), dropout=float(cfg.get("dropout", 0.1)))
        model.load_state_dict(ck["state_dict"], strict=True)
        model.eval()
        with torch.no_grad():
            scores_raw = model.attention_weights(torch.from_numpy(bag)).numpy()
        scores = _normalize(scores_raw)
        slide = openslide.OpenSlide(slide_path)
        title = f"{args.task} | {args.backbone} image_only | sample {sid} | fold{fold} | y=1 p={row['y_prob']:.3f}"
        stem = f"{sid}_fold{fold}"
        _overlay(slide, coords, scores, level, tile_size, title, out_dir / f"{stem}_heatmap_overlay.png")
        _tile_grid(slide, coords, scores_raw, list(np.argsort(-scores_raw)[:args.top_tiles]),
                   level, tile_size, out_dir / f"{stem}_top_tiles.png", f"Top tiles — {sid}")
        made.append(stem)
        print(f"  [ok] {sid} fold{fold} -> overlay + top tiles")
    print(f"wrote {len(made)} heatmap sets to {out_dir}")
    return 0 if made else 1


if __name__ == "__main__":
    raise SystemExit(main())
