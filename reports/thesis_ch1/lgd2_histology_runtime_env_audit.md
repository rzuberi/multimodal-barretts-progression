# LGD2+ Histology Runtime Environment Audit

- Pass: `True`
- Python executable: `/home/zuberi01/miniforge3/envs/pathology/bin/python`
- Python version: `3.10.18`
- Torch version: `2.7.1`
- Torch CUDA available: `False`
- OpenSlide Python version: `1.4.2`

## sys.path Head

- `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/multimodal-barretts-progression/scripts`
- `/home/zuberi01/miniforge3/envs/pathology/lib/python310.zip`
- `/home/zuberi01/miniforge3/envs/pathology/lib/python3.10`
- `/home/zuberi01/miniforge3/envs/pathology/lib/python3.10/lib-dynload`
- `/home/zuberi01/.local/lib/python3.10/site-packages`

## Dependencies

| dependency | required | import_success | version | status | error |
| --- | --- | --- | --- | --- | --- |
| torch | True | True | 2.7.1 | PASS |  |
| numpy | True | True | 1.26.0 | PASS |  |
| pandas | True | True | 2.3.2 | PASS |  |
| PIL | True | True | 12.0.0 | PASS |  |
| openslide | True | True | 1.4.2 | PASS |  |

## Recommendation

Runtime imports pass. Re-run path preflight, then attempt only `row_idx 0` before any second case or all-case run.
