#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_SNAPSHOTS = REPO_ROOT / "data_snapshots"
SOURCE_CAMPAIGNS = REPO_ROOT / "source_aggregates" / "campaigns"
SOURCE_REPORTS = REPO_ROOT / "source_aggregates" / "reports"
FIGURES = REPO_ROOT / "figures"


def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].fillna("").astype(str).str.replace("`", "", regex=False)
        df.loc[df[column] == "", column] = pd.NA
    return df


def load_csv(path: Path) -> pd.DataFrame:
    return clean_strings(pd.read_csv(path))


def write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def build_task_leader_modality_counts(task_leaders: pd.DataFrame) -> pd.DataFrame:
    return (
        task_leaders.groupby(["task_type", "best_modality"], dropna=False)
        .size()
        .reset_index(name="n_tasks")
        .sort_values(["task_type", "n_tasks", "best_modality"], ascending=[True, False, True])
    )


def build_critical_biopsy_summary() -> pd.DataFrame:
    sample = load_csv(SOURCE_REPORTS / "critical_biopsy_sample_level.csv")
    patient = load_csv(SOURCE_REPORTS / "critical_biopsy_patient_level.csv")
    sample["analysis_level"] = "biopsy_sample"
    patient["analysis_level"] = "patient_max_score"
    keep = [
        "analysis_level",
        "model_group",
        "n_eval",
        "n_progressors",
        "auc_progression",
        "fn_count_at_0.5",
        "fnr_at_0.5",
        "sensitivity_at_spec90",
        "sensitivity_at_spec95",
        "clinical_line",
    ]
    return pd.concat([sample[keep], patient[keep]], ignore_index=True)


def build_biopsy_patient_aggregation_summary() -> pd.DataFrame:
    df = load_csv(SOURCE_REPORTS / "biopsy_patient_aggregation_combined.csv")
    df = df[df["report_section"].isin(["task1_biopsy_aggregation", "task2_patient_aggregation"])].copy()
    df["best_strategy"] = df["aggregation_strategy"]
    if "from_biopsy_strategy" in df.columns:
        patient_mask = df["aggregation_level"].eq("patient") & df["from_biopsy_strategy"].notna()
        df.loc[patient_mask, "best_strategy"] = (
            df.loc[patient_mask, "from_biopsy_strategy"] + " -> " + df.loc[patient_mask, "aggregation_strategy"]
        )
    group_cols = ["task_name", "modality", "aggregation_level"]
    best_idx = df.groupby(group_cols)["auc"].idxmax()
    summary = (
        df.loc[best_idx, ["task_name", "modality", "aggregation_level", "best_strategy", "auc", "sensitivity", "specificity", "n_eval"]]
        .sort_values(["task_name", "aggregation_level", "auc"], ascending=[True, True, False])
        .reset_index(drop=True)
    )
    return summary


def build_distance_to_progression_summary() -> pd.DataFrame:
    horizon = load_csv(SOURCE_REPORTS / "progressor_detection_horizon_summary.csv")
    never = load_csv(SOURCE_REPORTS / "progressor_never_caught_summary.csv")
    merged = horizon.merge(
        never[
            [
                "task_name",
                "model_id",
                "n_progressor_patients_with_preprogression_biopsies",
                "n_never_caught_patients_maxscore_lt_0p5",
                "pct_never_caught",
            ]
        ],
        on=["task_name", "model_id"],
        how="left",
    )
    return merged[
        [
            "task_name",
            "modality",
            "encoder",
            "model_name",
            "biopsy_aggregation_strategy",
            "earliest_detection_horizon_distance",
            "pct_never_caught",
            "n_never_caught_patients_maxscore_lt_0p5",
            "n_progressor_patients_with_preprogression_biopsies",
            "horizon_definition",
        ]
    ].sort_values(["task_name", "pct_never_caught"])


def build_modality_weight_shift_summary():
    bins = load_csv(SOURCE_REPORTS / "modality_weight_binned_stats.csv")
    spearman = load_csv(SOURCE_REPORTS / "modality_weight_spearman.csv")
    early = bins[bins["time_bin"] == "181-365"][
        ["task_name", "mean_image_weight", "mean_cnv_weight", "mean_prediction_score"]
    ].rename(
        columns={
            "mean_image_weight": "early_mean_image_weight",
            "mean_cnv_weight": "early_mean_cnv_weight",
            "mean_prediction_score": "early_mean_prediction_score",
        }
    )
    late = bins[bins["time_bin"] == "1096+"][
        ["task_name", "mean_image_weight", "mean_cnv_weight", "mean_prediction_score"]
    ].rename(
        columns={
            "mean_image_weight": "late_mean_image_weight",
            "mean_cnv_weight": "late_mean_cnv_weight",
            "mean_prediction_score": "late_mean_prediction_score",
        }
    )
    summary = spearman.merge(early, on="task_name", how="left").merge(late, on="task_name", how="left")
    summary["delta_image_weight_near_minus_far"] = (
        summary["early_mean_image_weight"] - summary["late_mean_image_weight"]
    )
    return bins, summary.sort_values("task_name")


def save_figure(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_baseline_headline_auc(headline: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    categories = headline["task"].tolist()
    x = list(range(len(categories)))
    width = 0.25
    modality_specs = [
        ("best_multimodal_auc", "Multimodal", "#1b6ca8"),
        ("best_image_auc", "Image", "#c44536"),
        ("best_cnv_auc", "CNV", "#4f772d"),
    ]
    for idx, (column, label, color) in enumerate(modality_specs):
        y = headline[column].fillna(0).tolist()
        offset = (idx - 1) * width
        ax.bar([v + offset for v in x], y, width=width, label=label, color=color)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=20, ha="right")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("AUC")
    ax.set_title("March 4 Baseline Snapshot: Headline Task AUC Comparison")
    ax.legend(frameon=False)
    save_figure(fig, "figure1_baseline_headline_auc.png")


def plot_task_leader_counts(task_leader_counts: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    pivot = task_leader_counts.pivot(index="task_type", columns="best_modality", values="n_tasks").fillna(0)
    pivot = pivot[[c for c in ["multimodal", "image", "cnv"] if c in pivot.columns]]
    colors = {"multimodal": "#1b6ca8", "image": "#c44536", "cnv": "#4f772d"}
    pivot.plot(kind="bar", stacked=True, ax=ax, color=[colors[c] for c in pivot.columns], width=0.7)
    ax.set_ylabel("Tasks Led")
    ax.set_xlabel("")
    ax.set_title("Baseline Task Leaders by Modality and Task Type")
    ax.legend(title="Modality", frameon=False)
    save_figure(fig, "figure2_task_leader_counts.png")


def plot_atrisk_headline(atrisk: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    order = ["Top multimodal", "Top image-only", "Top CNV-only", "Top mixture-of-experts"]
    tasks = ["AtRisk_1y", "AtRisk_3y", "AtRisk_5y"]
    colors = {
        "Top multimodal": "#1b6ca8",
        "Top image-only": "#c44536",
        "Top CNV-only": "#4f772d",
        "Top mixture-of-experts": "#7a4cc2",
    }
    width = 0.18
    x = list(range(len(tasks)))
    for idx, category in enumerate(order):
        subset = (
            atrisk[atrisk["Category"] == category]
            .set_index("Task")
            .reindex(tasks)
            .reset_index()
        )
        offset = (idx - 1.5) * width
        ax.bar(
            [v + offset for v in x],
            subset["AUC"].tolist(),
            width=width,
            label=category.replace("Top ", "").replace("-of-", " "),
            color=colors[category],
        )
    ax.set_xticks(x)
    ax.set_xticklabels(tasks)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("AUC")
    ax.set_title("AtRisk No-Leak EPYC Relaunch: Top Models by Task")
    ax.legend(frameon=False, ncol=2)
    save_figure(fig, "figure3_atrisk_noleak_auc.png")


def plot_biopsy_patient_aggregation(summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    tasks = ["NextBiopsyProgression_LGD3plus", "Progressor_label"]
    colors = {"multimodal": "#1b6ca8", "image": "#c44536", "cnv": "#4f772d"}
    for ax, level in zip(axes, ["biopsy", "patient"]):
        subset = summary[summary["aggregation_level"] == level]
        task_labels = tasks
        x = list(range(len(task_labels)))
        width = 0.22
        for idx, modality in enumerate(["multimodal", "image", "cnv"]):
            rows = subset[subset["modality"] == modality].set_index("task_name").reindex(task_labels)
            ax.bar(
                [v + (idx - 1) * width for v in x],
                rows["auc"].tolist(),
                width=width,
                label=modality if ax is axes[0] else None,
                color=colors[modality],
            )
        ax.set_xticks(x)
        ax.set_xticklabels(["NextBiopsyProgression", "Progressor"], rotation=10)
        ax.set_title(f"Best {level.title()} Aggregation")
        ax.set_ylim(0.5, 1.0)
    axes[0].set_ylabel("AUC")
    axes[0].legend(frameon=False)
    fig.suptitle("Aggregation Analysis: Best AUC by Modality")
    save_figure(fig, "figure4_biopsy_patient_aggregation_auc.png")


def plot_critical_biopsy(critical: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    colors = ["#c44536", "#4f772d", "#1b6ca8", "#7a4cc2"]
    order = ["Top image-only", "Top CNV-only", "Best multimodal", "Best MoE"]
    for ax, level in zip(axes, ["biopsy_sample", "patient_max_score"]):
        subset = critical[critical["analysis_level"] == level].set_index("model_group").reindex(order).reset_index()
        positions = list(range(len(subset)))
        ax.bar(positions, subset["fn_count_at_0.5"], color=colors)
        ax.set_xticks(positions)
        ax.set_xticklabels(["Image", "CNV", "MM", "MoE"])
        ax.set_title("Biopsy-sample level" if level == "biopsy_sample" else "Patient level")
        ax.set_ylabel("False negatives at threshold 0.5")
    fig.suptitle("Critical Next-Biopsy Evaluation: Missed Positive Cases")
    save_figure(fig, "figure5_critical_biopsy_false_negatives.png")


def plot_distance_summary(distance: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    colors = {"image": "#c44536", "cnv": "#4f772d", "multimodal": "#1b6ca8"}
    order = distance.sort_values("pct_never_caught")["modality"].tolist()
    axes[0].bar(
        distance["modality"],
        distance["pct_never_caught"],
        color=[colors[m] for m in distance["modality"]],
    )
    axes[0].set_ylabel("% never caught")
    axes[0].set_title("Progressor Never-Caught Fraction")

    horizon_map = {"none": 0, "-1": 1, "-2": 2, "-3": 3, "-4": 4, "-5+": 5}
    axes[1].bar(
        distance["modality"],
        [horizon_map.get(v, 0) for v in distance["earliest_detection_horizon_distance"]],
        color=[colors[m] for m in distance["modality"]],
    )
    axes[1].set_yticks(list(horizon_map.values()))
    axes[1].set_yticklabels(["none", "-1", "-2", "-3", "-4", "-5+"])
    axes[1].set_title("Farthest Detection Horizon")
    fig.suptitle("Progressor Distance-to-Progression Summary")
    save_figure(fig, "figure6_distance_to_progression.png")


def plot_modality_weight_shift(bins: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    time_order = ["181-365", "366-730", "731-1095", "1096+"]
    display_labels = ["181-365", "366-730", "731-1095", "1096+"]
    for ax, task_name in zip(axes, ["Progressor_label", "NextBiopsyProgression_LGD3plus"]):
        subset = bins[bins["task_name"] == task_name].set_index("time_bin").reindex(time_order).reset_index()
        ax.plot(display_labels, subset["mean_image_weight"], marker="o", color="#1b6ca8", label="Image weight")
        ax.plot(display_labels, subset["mean_cnv_weight"], marker="o", color="#4f772d", label="CNV weight")
        ax.set_ylim(0, 1.0)
        ax.set_title(task_name.replace("_LGD3plus", ""))
        ax.set_xlabel("Days-to-progression bin")
    axes[0].set_ylabel("Mean modality weight proxy")
    axes[0].legend(frameon=False)
    fig.suptitle("Modality Reliance Across Pre-Progression Time Bins")
    save_figure(fig, "figure7_modality_weight_shift.png")


def main() -> None:
    DATA_SNAPSHOTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)

    headline = load_csv(DATA_SNAPSHOTS / "headline_task_auc_comparison.csv")
    task_leaders = load_csv(DATA_SNAPSHOTS / "task_leaders.csv")
    task_leader_counts = build_task_leader_modality_counts(task_leaders)
    atrisk = load_csv(SOURCE_REPORTS / "atrisk_noleak_top_models.csv")
    critical = build_critical_biopsy_summary()
    aggregation = build_biopsy_patient_aggregation_summary()
    distance = build_distance_to_progression_summary()
    modality_bins, modality_summary = build_modality_weight_shift_summary()
    fusion_counts = load_csv(SOURCE_REPORTS / "fusion_rescue_hurt_counts.csv")

    outputs = {
        "task_leader_modality_counts.csv": task_leader_counts,
        "atrisk_noleak_headline_models.csv": atrisk,
        "critical_biopsy_headline.csv": critical,
        "biopsy_patient_aggregation_best.csv": aggregation,
        "distance_to_progression_summary.csv": distance,
        "fusion_rescue_hurt_group_counts.csv": fusion_counts,
        "modality_weight_time_bins.csv": modality_bins,
        "modality_weight_shift_summary.csv": modality_summary,
    }
    for name, df in outputs.items():
        write_csv(df, DATA_SNAPSHOTS / name)

    plot_baseline_headline_auc(headline)
    plot_task_leader_counts(task_leader_counts)
    plot_atrisk_headline(atrisk)
    plot_biopsy_patient_aggregation(aggregation)
    plot_critical_biopsy(critical)
    plot_distance_summary(distance)
    plot_modality_weight_shift(modality_bins)


if __name__ == "__main__":
    main()
