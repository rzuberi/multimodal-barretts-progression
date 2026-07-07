# LGD2+ Histology Candidate Environments

- Candidates tested: 11
- Passing candidates: 3
- Selected Python executable: `/home/zuberi01/miniforge3/envs/pathology/bin/python`
- Selection reason: `pathology` is the most pathology/WSI-aligned passing env; `.conda_mil` timed out during preflight.

## Candidates

| candidate_id | python_path | exists | python_version | torch | torch_version | CUDA | numpy | pandas | PIL | openslide | overall_pass | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| env_01 | /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/.conda_mil/bin/python | True | 3.10.19 | False |  |  | False | False | False | False | False | runtime preflight timed out after 60s |
| env_02 | /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/.conda_mil/bin/python3 | True | 3.10.19 | False |  |  | False | False | False | False | False | runtime preflight timed out after 60s |
| env_03 | /home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python | True | 3.12.13 | False |  |  | True | True | False | False | False | runtime_env_pass=False python=/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python |
| env_04 | /home/zuberi01/miniforge3/envs/erin/bin/python | True | 3.10.19 | True | 2.0.1+cu117 | False | True | True | True | True | True | runtime_env_pass=True python=/home/zuberi01/miniforge3/envs/erin/bin/python |
| env_05 | /home/zuberi01/miniforge3/envs/llm_contrib_game/bin/python | True | 3.11.14 | False |  |  | False | False | False | False | False | no audit csv; Traceback (most recent call last):   File "/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/multimodal-barretts-progression/scripts/11_validate_histology_runtime_env.py", line 11, in <module>     import pandas as pd ModuleNotFoundError: No module named 'pandas' |
| env_06 | /home/zuberi01/miniforge3/envs/llm_ollama/bin/python | True | 3.11.14 | False |  |  | True | True | True | False | False | runtime_env_pass=False python=/home/zuberi01/miniforge3/envs/llm_ollama/bin/python |
| env_07 | /home/zuberi01/miniforge3/envs/nnunetv2/bin/python | True | 3.10.19 | True | 2.9.1+cu128 | False | True | True | True | False | False | runtime_env_pass=False python=/home/zuberi01/miniforge3/envs/nnunetv2/bin/python |
| env_08 | /home/zuberi01/miniforge3/envs/pathology/bin/python | True | 3.10.18 | True | 2.7.1 | False | True | True | True | True | True | runtime_env_pass=True python=/home/zuberi01/miniforge3/envs/pathology/bin/python |
| env_09 | /home/zuberi01/miniforge3/envs/stardist/bin/python | True | 3.10.19 | False |  |  | False | False | False | False | False | no audit csv; Traceback (most recent call last):   File "/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/multimodal-barretts-progression/scripts/11_validate_histology_runtime_env.py", line 11, in <module>     import pandas as pd ModuleNotFoundError: No module named 'pandas' |
| env_10 | /home/zuberi01/miniforge3/envs/takehome-ml/bin/python | True | 3.11.14 | False |  |  | False | False | False | False | False | no audit csv; Traceback (most recent call last):   File "/home/zuberi01/miniforge3/envs/takehome-ml/lib/python3.11/site-packages/pandas/__init__.py", line 22, in <module>     from pandas.compat import (   File "/home/zuberi01/miniforge3/envs/takehome-ml/lib/python3.11/site-packages/pandas/compat/__init__.py", line 27, in <module>     from pandas.compat.numpy import is_numpy_dev   File "/home/zuberi01/miniforge3/envs/takehome-ml/lib/python3.11/site-packages/pandas/compat/numpy/__init__.py", line  |
| env_11 | /home/zuberi01/miniforge3/envs/virchow2/bin/python | True | 3.10.19 | True | 2.9.1+cu128 | False | True | True | True | True | True | runtime_env_pass=True python=/home/zuberi01/miniforge3/envs/virchow2/bin/python |
