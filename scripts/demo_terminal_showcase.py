#!/usr/bin/env python3

import argparse
import sys
import termios
import time
import tty


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[37m"

EXPECTED_CLONE = "git clone https://github.com/rzuberi/multimodal-barretts-progression"
EXPECTED_CD = "cd multimodal-barretts-progression"
EXPECTED_TRAIN = (
    "python train_model.py --config configs/example.yaml "
    "--dataset data/demo_patient_cohort.csv --fusion multimodal_transformer"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Deterministic terminal showcase for screen-recorded demos."
    )
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier. Higher is faster.")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors.")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear the screen at startup.")
    parser.add_argument("--auto", action="store_true", help="Autoplay the full sequence without waiting for input.")
    parser.add_argument(
        "--compact-prompt",
        action="store_true",
        help="Use shorter prompts to avoid line wrapping during demos.",
    )
    return parser.parse_args()


def color(text, code, enabled):
    if not enabled:
        return text
    return code + text + RESET


def normalize_command(text):
    return " ".join(str(text).strip().split())


class Demo:
    def __init__(self, speed, use_color, compact_prompt):
        self.sleep_scale = 1.0 / max(speed, 0.01)
        self.use_color = use_color
        self.fill_char_delay = 0.045 * self.sleep_scale
        self.compact_prompt = compact_prompt

    def pause(self, seconds):
        time.sleep(seconds * self.sleep_scale)

    def write(self, text, end=""):
        sys.stdout.write(text + end)
        sys.stdout.flush()

    def println(self, text=""):
        self.write(text, end="\n")

    def section(self, title):
        self.println()
        self.println(color(title, BOLD + CYAN, self.use_color))
        self.pause(0.25)

    def prompt(self, in_repo):
        if self.compact_prompt:
            if in_repo:
                return color("demo@multimodal:~/mbp$ ", BOLD + GREEN, self.use_color)
            return color("demo@multimodal:~$ ", BOLD + GREEN, self.use_color)
        if in_repo:
            return color("demo@multimodal:~/multimodal-barretts-progression$ ", BOLD + GREEN, self.use_color)
        return color("demo@multimodal:~$ ", BOLD + GREEN, self.use_color)

    def info(self, text):
        self.println(color(text, DIM + WHITE, self.use_color))

    def note(self, text):
        self.println(color(text, DIM + CYAN, self.use_color))

    def fill_buffer(self, command):
        for ch in command:
            self.write(ch)
            time.sleep(self.fill_char_delay)


def progress_bar(frac, width):
    done = int(round(frac * width))
    done = max(0, min(done, width))
    return "[" + ("#" * done) + ("-" * (width - done)) + "]"


def print_intro(demo):
    demo.println(color("Multimodal Barrett's Progression Demo", BOLD + WHITE, demo.use_color))
    demo.println(color("Interactive scripted shell for screen recording", DIM + WHITE, demo.use_color))
    demo.pause(0.5)


def print_clone_output(demo):
    clone_lines = [
        "Cloning into 'multimodal-barretts-progression'...",
        "remote: Enumerating objects: 248, done.",
        "remote: Counting objects: 100% (248/248), done.",
        "remote: Compressing objects: 100% (121/121), done.",
        "Receiving objects: 100% (248/248), 5.42 MiB | 7.84 MiB/s, done.",
        "Resolving deltas: 100% (119/119), done.",
    ]
    for line in clone_lines:
        demo.info(line)
        demo.pause(0.18)


def print_training_output(demo):
    demo.section("Loading Demo Configuration")
    config_lines = [
        "task: early progression detection",
        "samples: 1,248 biopsies",
        "patients: 214",
        "modalities: histopathology + CNV + longitudinal timeline",
        "validation: patient-disjoint 5-fold",
        "hardware: 1x GPU  |  mixed precision enabled",
    ]
    for line in config_lines:
        label, value = line.split(":", 1)
        demo.println("  " + color(label + ":", BOLD + BLUE, demo.use_color) + color(value, WHITE, demo.use_color))
        demo.pause(0.12)

    demo.section("Reference Baselines")
    demo.println("  image-only validation AUC      " + color("0.842", YELLOW, demo.use_color))
    demo.println("  CNV-only validation AUC        " + color("0.801", YELLOW, demo.use_color))
    demo.println("  multimodal target              " + color("> 0.880", GREEN, demo.use_color))
    demo.pause(0.8)

    demo.section("Training Multimodal Model")

    epoch_rows = [
        (1, 0.681, 0.742, -0.100, -0.059),
        (2, 0.603, 0.781, -0.061, -0.020),
        (3, 0.548, 0.812, -0.030, +0.011),
        (4, 0.501, 0.838, -0.004, +0.037),
        (5, 0.462, 0.857, +0.015, +0.056),
        (6, 0.431, 0.872, +0.030, +0.071),
        (7, 0.409, 0.884, +0.042, +0.083),
        (8, 0.392, 0.893, +0.051, +0.092),
        (9, 0.381, 0.901, +0.059, +0.100),
        (10, 0.373, 0.904, +0.062, +0.103),
    ]

    for epoch, loss, val_auc, gain_img, gain_cnv in epoch_rows:
        bar = progress_bar(float(epoch) / 10.0, 24)
        line = (
            "  Epoch {epoch:02d}/10  {bar}  loss={loss:.3f}  val_auc={val_auc:.3f}  "
            "vs_image={gain_img:+.3f}  vs_cnv={gain_cnv:+.3f}"
        ).format(
            epoch=epoch,
            bar=color(bar, MAGENTA, demo.use_color),
            loss=loss,
            val_auc=val_auc,
            gain_img=gain_img,
            gain_cnv=gain_cnv,
        )
        demo.println(line)
        demo.pause(0.34)

    demo.section("Evaluation Summary")
    demo.println(color("  Best validation epoch: 10", BOLD + WHITE, demo.use_color))
    demo.println("  image-only AUC        " + color("0.842", YELLOW, demo.use_color))
    demo.println("  CNV-only AUC          " + color("0.801", YELLOW, demo.use_color))
    demo.println("  multimodal AUC        " + color("0.904", BOLD + GREEN, demo.use_color))
    demo.println("  gain vs image-only    " + color("+0.062", GREEN, demo.use_color))
    demo.println("  gain vs CNV-only      " + color("+0.103", GREEN, demo.use_color))
    demo.pause(0.8)

    demo.section("Clinical Output Snapshot")
    clinical_lines = [
        "high-risk patients flagged early: 31 / 37",
        "false negatives reduced vs image-only: 18%",
        "false negatives reduced vs CNV-only:   29%",
        "patient-level ranking stability:       0.91",
    ]
    for line in clinical_lines:
        key, value = line.split(":", 1)
        demo.println("  " + color(key + ":", BOLD + CYAN, demo.use_color) + color(value, WHITE, demo.use_color))
        demo.pause(0.14)

    demo.section("Artifacts")
    artifact_lines = [
        ("saved model", "outputs/demo_multimodal/model.pt"),
        ("metrics report", "outputs/demo_multimodal/metrics.json"),
        ("risk table", "outputs/demo_multimodal/patient_risk_scores.csv"),
        ("run status", "complete"),
    ]
    for label, value in artifact_lines:
        demo.println("  " + color(label, BOLD + BLUE, demo.use_color) + "  " + color(value, WHITE, demo.use_color))
        demo.pause(0.12)

    demo.println()
    demo.println(color("Demo complete. Ready for Q&A or a second run.", BOLD + GREEN, demo.use_color))


def is_expected_clone(command):
    return normalize_command(command) == normalize_command(EXPECTED_CLONE)


def is_expected_cd(command):
    return normalize_command(command) == normalize_command(EXPECTED_CD)


def is_expected_train(command):
    cmd = normalize_command(command)
    return cmd.startswith("python train_model.py ") or cmd == normalize_command(EXPECTED_TRAIN)


def interactive_loop(demo):
    in_repo = False
    clone_done = False
    train_done = False

    demo.note("Type the demo commands live. Use Ctrl+C to exit.")
    demo.note("Expected flow: clone -> cd -> python train_model.py ...")
    demo.note("Shortcuts: press 1 for clone, 2 for cd, 3 for train command, then hit Enter.")

    shortcuts = {
        "1": EXPECTED_CLONE,
        "2": EXPECTED_CD,
        "3": EXPECTED_TRAIN,
    }

    def read_command(prompt):
        if not sys.stdin.isatty():
            return input(prompt)

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        buffer_chars = []
        try:
            tty.setraw(fd)
            demo.write(prompt)
            while True:
                ch = sys.stdin.read(1)
                if ch in ("\r", "\n"):
                    demo.println()
                    return "".join(buffer_chars)
                if ch == "\x03":
                    raise KeyboardInterrupt
                if ch == "\x04":
                    if not buffer_chars:
                        demo.println()
                        raise EOFError
                    continue
                if ch in ("\x7f", "\b"):
                    if buffer_chars:
                        buffer_chars.pop()
                        demo.write("\b \b")
                    continue
                if ch == "\x1b":
                    seq = sys.stdin.read(2)
                    if seq == "[3":
                        sys.stdin.read(1)
                    continue
                if not buffer_chars and ch in shortcuts:
                    command = shortcuts[ch]
                    buffer_chars = list(command)
                    demo.fill_buffer(command)
                    continue
                if ch.isprintable():
                    buffer_chars.append(ch)
                    demo.write(ch)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    while True:
        try:
            command = read_command(demo.prompt(in_repo))
        except EOFError:
            demo.println()
            break

        cmd = normalize_command(command)
        if not cmd:
            continue
        if cmd in ("exit", "quit"):
            break
        if cmd == "help":
            demo.note("Try:")
            demo.note("  " + EXPECTED_CLONE)
            demo.note("  " + EXPECTED_CD)
            demo.note("  " + EXPECTED_TRAIN)
            continue
        if cmd == "clear":
            demo.write("\033[2J\033[H")
            print_intro(demo)
            continue

        if not clone_done:
            if is_expected_clone(cmd):
                print_clone_output(demo)
                clone_done = True
                continue
            demo.note("Demo is waiting for the clone command.")
            continue

        if clone_done and not in_repo:
            if is_expected_cd(cmd):
                in_repo = True
                continue
            demo.note("Demo is waiting for: cd multimodal-barretts-progression")
            continue

        if in_repo and not train_done:
            if is_expected_train(cmd):
                print_training_output(demo)
                train_done = True
                continue
            demo.note("Demo is waiting for a python train_model.py command.")
            continue

        demo.note("Demo finished. Type 'clear' to restart or 'exit' to quit.")


def autoplay(demo):
    steps = [
        (False, EXPECTED_CLONE, print_clone_output),
        (False, EXPECTED_CD, None),
        (True, EXPECTED_TRAIN, print_training_output),
    ]
    in_repo = False
    for step_in_repo, command, action in steps:
        demo.println(demo.prompt(step_in_repo) + command)
        demo.pause(0.35)
        if action is not None:
            action(demo)
        in_repo = step_in_repo
    return in_repo


def main():
    args = parse_args()
    demo = Demo(speed=args.speed, use_color=not args.no_color, compact_prompt=args.compact_prompt)

    if not args.no_clear:
        demo.write("\033[2J\033[H")

    print_intro(demo)
    if args.auto:
        autoplay(demo)
    else:
        interactive_loop(demo)


if __name__ == "__main__":
    main()
