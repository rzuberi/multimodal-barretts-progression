#!/usr/bin/env bash
set -euo pipefail

bad_ext='(\.csv|\.tsv|\.xlsx|\.xls|\.jsonl|\.sqlite|\.db|\.pt|\.pth|\.ckpt|\.h5|\.hdf5|\.npy|\.npz|\.pkl|\.pickle|\.svs|\.ndpi|\.tif|\.tiff|\.png|\.jpg|\.jpeg|\.pdf)$'
bad_dirs='(^|/)(data|raw_data|derived_data|results|checkpoints|models|embeddings|features)(/|$)'

tracked="$(git ls-files | grep -v '^docs/final_results_manifest\.csv$' || true)"

if printf '%s\n' "$tracked" | grep -E "$bad_ext" >/dev/null; then
  printf 'Forbidden data-like tracked files:\n' >&2
  printf '%s\n' "$tracked" | grep -E "$bad_ext" >&2
  exit 1
fi

if printf '%s\n' "$tracked" | grep -E "$bad_dirs" >/dev/null; then
  printf 'Forbidden data/result directories tracked:\n' >&2
  printf '%s\n' "$tracked" | grep -E "$bad_dirs" >&2
  exit 1
fi

printf 'OK: no forbidden data-like files are tracked.\n'
