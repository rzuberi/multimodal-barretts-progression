# LGD2+ Histology Path Remap Audit

- Cases checked: 8
- Fully resolvable cases: 8
- Dry-run can proceed in this shell: `True`
- Config source: `configs/path_remap.template.yaml (template fallback)`
- Master table resolved: `True` via `candidate_root:/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training`
- Feature index resolved: `True` via `candidate_root:/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training`

## Missing Required Fields

- None.

## Remap Rules Attempted

- `/scratchc/fmlab/datasets/imaging/` -> `/mnt/scratchc/fmlab/datasets/imaging/`
- `/scratchc/fmlab/zuberi01/phd/barretts_retraining/` -> `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/`
- `/scratchc/fmlab/` -> `/mnt/scratche/slow/fmlab/`

## Candidate Roots

- `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining`
- `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/data/foundation_outputs`
- `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training`
- `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/data`
- `/mnt/scratchc`
- `/scratchc`
- `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training`
- `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/data`

## Required Missing Rows

_No rows._

## Next Action

Path validation passed for required dry-run fields. A case-level WSI dry run can be attempted externally.
