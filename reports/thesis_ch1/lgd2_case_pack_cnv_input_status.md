# LGD2+ Case-Pack CNV Input Status

CNV interpretation is not ready for the first case-pack cases because LGD2+ feature importance and gene-map inputs have not been validated.

| case_id | cnv_profile_ref | fold | can_generate_now | blocker |
| --- | --- | --- | --- | --- |
| `A_true_positive_early_02` | `SLX-12455.D701_D504` | `fold2` | `False` | LGD2+ selected-case CNV feature matrix/model/importances/window-to-gene map not validated; existing CNV summaries are missing or legacy only. |
| `B_false_negative_07` | `SLX-13692.D703_D508` | `fold3` | `False` | LGD2+ selected-case CNV feature matrix/model/importances/window-to-gene map not validated; existing CNV summaries are missing or legacy only. |
| `E_cnv_rescue_19` | `SLX-12451.D710_D506` | `fold4` | `False` | LGD2+ selected-case CNV feature matrix/model/importances/window-to-gene map not validated; existing CNV summaries are missing or legacy only. |

Exact next step: validate LGD2+ CNV feature matrix, saved estimator/worklist, and window-to-gene map, then run the CNV command templates in `lgd2_cnv_interpretation_commands.md` into the external analysis root.
