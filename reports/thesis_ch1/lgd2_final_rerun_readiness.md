# LGD2+ Final Rerun Readiness

Release `chapter1_lgd2_final_pre_event_20260713_final`. Overall: **PASS** (12/12 gates).

| gate | status | detail |
| --- | --- | --- |
| endpoint_agreement | PASS | disagreements=0 |
| cohort_not_blocked | PASS | blocked=False |
| strict_pre_event_derived | PASS | eligible_rows=707 |
| no_current_or_post_event_in_eligible | PASS | at/post-event rows excluded by construction |
| A_matched_rowset_equality | PASS | equal=True |
| B_single_frozen_split | PASS | split_problems=[] |
| enough_pos_neg_per_fold | PASS | [{'outer_fold': 1, 'positive_patients': 10, 'negative_patients': 20}, {'outer_fold': 2, 'positive_patients': 10, 'negati |
| leakage_and_contract_tests | PASS | 23 passed in 1.22s |
| release_external_to_git | PASS | /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/chapter1_lgd2_final_pre_event_20260 |
| no_raw_data_tracked | PASS | OK: no forbidden data-like files are tracked. |
| output_non_overwrite | PASS | scripts 17/18 refuse overwrite without --overwrite |
| candidate_registry_present | PASS | configs/chapter1_lgd2_final_analysis.yaml |

Do not launch expensive jobs unless every gate is PASS.
