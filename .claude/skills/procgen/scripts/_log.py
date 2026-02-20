import sys
import time
from pathlib import Path

BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

_start = None
_progress = Path(__file__).resolve().parent / "_progress.log"


def _write(line):
    with open(_progress, "a", encoding="utf-8") as f:
        f.write(f"{time.time():.1f} {line}\n")


def init():
    _progress.unlink(missing_ok=True)
    _write("PIPELINE START")


def stage(name):
    global _start
    bar = "\u2500" * max(40 - len(name) - 2, 4)
    print(f"\n{BOLD}{CYAN}\u2500\u2500\u2500 {name} {bar}{RESET}", file=sys.stderr, flush=True)
    _write(f"STAGE {name}")
    _start = time.time()


def haiku(func):
    print(f"  {YELLOW}>> haiku:{RESET} {func}", file=sys.stderr, flush=True)
    _write(f"LLM {func}")


def detail(msg):
    print(f"  {DIM}{msg}{RESET}", file=sys.stderr, flush=True)


def ok(msg):
    print(f"  {GREEN}+ {msg}{RESET}", file=sys.stderr, flush=True)
    _write(f"OK {msg}")


def fail(msg):
    print(f"  {RED}x {msg}{RESET}", file=sys.stderr, flush=True)
    _write(f"FAIL {msg}")


def elapsed():
    if _start is None:
        return
    dt = time.time() - _start
    print(f"  {MAGENTA}({dt:.1f}s){RESET}", file=sys.stderr, flush=True)
    _write(f"ELAPSED {dt:.1f}s")
