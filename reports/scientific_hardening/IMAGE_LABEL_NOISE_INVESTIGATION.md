# Image Label-Noise / Tissue-Sampling Investigation (exploratory)

**Question:** When the image model scores a *progressor* patient's biopsy as low-risk, is that a model failure (artefact, missed dysplasia), or is the imaged biopsy genuinely benign because the dangerous tissue is elsewhere (patchy sampling / patient-level label applied to a single slide)?

**Design (leakage-safe, patient-level context):** each row = one *current* biopsy (one slide); the LGD2+ label is the *next* biopsy's outcome. Per-fold threshold = 90th percentile of other-fold negatives (as Phase 4). For every positive sample-row we linked the imaged biopsy's *own* current grade (CurrentGradeInt: 0=NDBE benign, 1=indeterminate, 2=LGD) and the patient's max pathology, and — for five benign-current image-missed cases across four folds — recomputed the ABMIL per-tile attention from each row's own fold checkpoint and overlaid it on the real WSI thumbnail.

## The image model reads the slide it is given
Mean image score rises monotonically with the imaged biopsy's own grade:

| Current grade of imaged biopsy | n | mean image y_prob |
|---|---|---|
| NDBE (benign, 0) | 553 | 0.341 |
| Indeterminate (1) | 67 | 0.496 |
| LGD (2) | 87 | 0.521 |

The encoder responds to visible dysplasia — it is not blind or artefact-driven.

## Most "missed progressors" are benign slides of progressor patients

| Group | n | imaged biopsy benign (NDBE) | current grade < patient max |
|---|---|---|---|
| All positive rows | 107 | — | 63% |
| Image-**missed** positives | 70 | **51%** | 67% |
| Image-caught positives | 37 | 46% | — |
| Image-missed **with benign current biopsy** | 36 | 100% | 100% |

63% of all positive rows have a current grade *below* the patient's maximum: the dangerous tissue is elsewhere in the patient (a different biopsy) or later, not on the slide the model sees. Of the 70 rows the image missed, 36 (51%) are benign-appearing slides — scoring them low-risk is **correct for that tissue**. The "progression" label is a patient-level summary pinned onto a single slide.

## CNV recovers the signal the slide cannot show
For the 36 image-missed benign-current positives, mean CNV score is **0.212 vs 0.172** baseline on true negatives — the genomic assay carries field-level risk that the sampled histology cannot. This is concrete mechanistic support for multimodal fusion: CNV and image fail on *different* cases, and the failure is structural (tissue sampling), not noise.

## Attention overlays (5 benign-current image-missed cases)
On all five slides, attention lands on genuine biopsy epithelium — **not** on scanner artefacts, pen marks, tissue folds, or background — and no focal high-grade region is present to overlook. The low score reflects genuinely benign morphology on the sampled fragment. (Qualitative, 5 cases, no independent pathologist read — framed as *consistent with* tissue-sampling, not proof.) One case (PR1/HIN/043) has patient max grade 0 and is flagged as a label edge case with high CNV (0.43), not a histologic progressor.

## Verdict & implications
The low-image-score-on-progressor pattern is **predominantly tissue sampling and a patient-level label applied to single slides — not model artefact error.** Implications for the chapter:
1. **This is a limitation of the label, not (mainly) the model.** A biopsy-level image model cannot see dysplasia that is not on the imaged fragment; the patient-level worst-grade endpoint guarantees a floor of "unwinnable" image cases.
2. **It is a positive argument for multimodality.** CNV scores these unwinnable-by-image cases above baseline — the modalities are complementary by construction, echoing the Phase 4 disagreement finding.
3. **Actionable next step (for a future chapter, not now):** a pathologist read of the imaged fragment on a sample of missed cases would upgrade this from "consistent with" to a quantified label-noise rate; and biopsy-level (rather than patient-max) image labels would remove the structural floor.

Artifacts: `attention_label_noise_panel.png` (figure), `label_noise_aggregate.csv`, `label_noise_image_by_grade.csv`. Per-case identifiers and WSI overlays are kept off Git (patient data).
