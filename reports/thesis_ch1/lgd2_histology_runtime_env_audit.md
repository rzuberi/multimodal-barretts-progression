# LGD2+ Histology Runtime Environment Audit

- Pass: `False`
- Python executable: `/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python`
- Python version: `3.12.13`
- Torch version: ``
- Torch CUDA available: ``
- OpenSlide Python version: ``

## sys.path Head

- `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/multimodal-barretts-progression/scripts`
- `/home/zuberi01/miniforge3/envs/barretts_multimodal/lib/python312.zip`
- `/home/zuberi01/miniforge3/envs/barretts_multimodal/lib/python3.12`
- `/home/zuberi01/miniforge3/envs/barretts_multimodal/lib/python3.12/lib-dynload`
- `/home/zuberi01/.local/lib/python3.12/site-packages`

## Dependencies

| dependency | required | import_success | version | status | error |
| --- | --- | --- | --- | --- | --- |
| torch | True | False |  | FAIL | ModuleNotFoundError: No module named 'torch' |
| numpy | True | True | 2.4.4 | PASS |  |
| pandas | True | True | 3.0.1 | PASS |  |
| PIL | True | False |  | FAIL | ModuleNotFoundError: No module named 'PIL' |
| openslide | True | False |  | FAIL | ModuleNotFoundError: No module named 'openslide' |

## Recommendation

Do not rerun WSI explainability from this environment. Missing imports: `torch`, `PIL`, `openslide`.
