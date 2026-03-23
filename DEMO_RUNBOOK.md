# Demo Runbook

Launch the terminal demo with:

```bash
python3 scripts/demo_terminal_showcase.py
```

Useful variants:

```bash
python3 scripts/demo_terminal_showcase.py --speed 1.5
python3 scripts/demo_terminal_showcase.py --speed 2.0 --no-clear
python3 scripts/demo_terminal_showcase.py --no-type
```

What it does:

- simulates cloning the public repo
- simulates entering the repo directory
- simulates a headless training command
- shows deterministic 10-epoch progress output
- ends with a polished multimodal vs unimodal result summary

This is a scripted demo, so the output is always the same and is designed for screen recording.
