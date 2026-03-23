# Demo Runbook

Launch the interactive terminal demo with:

```bash
python3 scripts/demo_terminal_showcase.py
```

Then type or paste these commands during the recording:

```bash
git clone https://github.com/rzuberi/multimodal-barretts-progression
cd multimodal-barretts-progression
python train_model.py --config configs/example.yaml --dataset data/demo_patient_cohort.csv --fusion multimodal_transformer
```

Useful variants:

```bash
python3 scripts/demo_terminal_showcase.py --speed 1.5
python3 scripts/demo_terminal_showcase.py --auto
python3 scripts/demo_terminal_showcase.py --speed 2.0 --no-clear
```

What it does:

- waits for you to type the demo commands live
- simulates cloning the public repo
- simulates entering the repo directory
- simulates a headless training command
- shows deterministic 10-epoch progress output
- ends with a polished multimodal vs unimodal result summary

This is a scripted demo, so the output is always the same and is designed for screen recording.
