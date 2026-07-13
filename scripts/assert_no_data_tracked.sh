#!/usr/bin/env bash
set -euo pipefail

bad_ext='(\.csv|\.tsv|\.xlsx|\.xls|\.jsonl|\.sqlite|\.db|\.pt|\.pth|\.ckpt|\.h5|\.hdf5|\.npy|\.npz|\.pkl|\.pickle|\.svs|\.ndpi|\.tif|\.tiff|\.png|\.jpg|\.jpeg|\.pdf)$'
bad_dirs='(^|/)(data|raw_data|derived_data|results|checkpoints|models|embeddings|features)(/|$)'

tracked="$(
  git ls-files \
    | grep -v '^docs/final_results_manifest\.csv$' \
    | grep -v '^src/barrett/data/' \
    | grep -v '^reports/thesis_ch1/lgd2_patient_level_metrics_all_samples\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_patient_level_metrics_early_prediction_only\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_cohort_flow\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_main_model_comparison\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_early_prediction_model_comparison\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_interpretation_case_selection\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_final_interpretation_case_subset\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_modality_case_summary\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_cnv_interpretation_summary\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_wsi_case_manifest\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_interpretation_summary\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_dry_run_cases\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_dry_run_execution_status\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_dry_run_summary\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_path_remap_audit\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_runtime_env_audit\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_candidate_envs\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_row0_output_audit\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_row0_interpretation_summary\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_row1_output_audit\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_row1_interpretation_summary\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_remaining6_cases\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_all8_output_audit\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_all8_interpretation_summary\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_histology_final_figure_candidates\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_multimodal_case_pack_selection\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_fusion_case_interpretation\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_case_pack_histology_panel_inventory\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_case_pack_cnv_input_status\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_case_pack_cnv_top_windows\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_modality_ablation_comparison\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_paired_model_differences_all_samples\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_final_pre_event_cohort_flow\.csv$' \
    | grep -v '^reports/thesis_ch1/lgd2_paired_model_differences_early_prediction_only\.csv$' \
    || true
)"

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
