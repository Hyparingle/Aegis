"""Aegis V1 - repeatedly stops user-chosen bloatware processes to free PC resources.

Windows only.
  Normal run : python aegis.py        (asks for a login: 'user' or the dev secret)
  Debug tool : python aegis.py debug   (dev-only diagnostics)

The process list and credentials below are baked into the (obfuscated) build.
"""

import csv
import io
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime

# ANSI colours
RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"

PROMPT = f"{BOLD}aegis>{RESET} "

# Bump on each release. Shown under the banner at startup.
VERSION = "1.1"

# ---------------------------------------------------------------------------
# CONFIG  (baked into the obfuscated build)
# ---------------------------------------------------------------------------
PROCESSES = [
    "BackdropClient.exe",
    "StudentKeeper.exe",
    "ContentKeeper.exe",
    "screenscanning.exe"
]

CHECK_INTERVAL = 2      # seconds between normal sweeps

# Logins (all lowercase). NOTE: obfuscation is a deterrent, not secure storage -
# the dev secret is a throwaway, not a real password.
NORMAL_LOGIN = "user"
DEV_LOGIN = "aegis-dev~~7"

# "Hammer until dead" settings for fast-respawning processes.
MAX_RETRIES = 5         # rapid re-kills after the first hit
HAMMER_DELAY = 0.3      # seconds between rapid re-checks
# ---------------------------------------------------------------------------

BANNER = r"""
   _   ___ ___ ___ ___
  /_\ | __/ __|_ _/ __|
 / _ \| _| (_ || |\__ \
/_/ \_\___\___|___|___/
"""


def print_banner():
    print(f"{CYAN}{BOLD}{BANNER}{RESET}")
    print(f"{DIM}        you know why you're here{RESET}")
    print(f"{DIM}        v{VERSION}{RESET}\n")


def clear_screen():
    """Wipe the console (incl. scrollback) so a typed dev secret can't be read back."""
    subprocess.run(["cmd", "/c", "cls"])


def close_console():
    """Close the cmd window Aegis is running in (used after a failed login)."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/PID", str(os.getppid())],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    sys.exit(1)  # fallback if the window didn't close (e.g. not launched from cmd)


def is_running(process_name):
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
        capture_output=True,
        text=True,
    )
    return process_name.lower() in result.stdout.lower()


def kill_process(process_name):
    subprocess.run(
        ["taskkill", "/F", "/IM", process_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def hammer(process):
    """Kill a process, then rapid-retry until it stays dead.

    Returns (was_running, dead, attempts). Shared by quiet and dev sweeps.
    """
    if not is_running(process):
        return (False, True, 0)

    kill_process(process)
    attempts = 1
    dead = False
    for _ in range(MAX_RETRIES):
        time.sleep(HAMMER_DELAY)
        if not is_running(process):
            dead = True
            break
        kill_process(process)
        attempts += 1
    return (True, dead, attempts)


# ---------------------------------------------------------------------------
# Resource view (dev console) - memory only, from tasklist. No deps, no admin.
# ---------------------------------------------------------------------------
def _parse_kb(mem_field):
    """'123,456 K' -> 123456 (KB). Returns None if there's no number (e.g. 'N/A')."""
    digits = "".join(c for c in mem_field if c.isdigit())
    return int(digits) if digits else None


def top_memory(limit):
    """Top image names by total memory. Returns [(name, (total_kb, count)), ...]."""
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
    )
    totals = {}  # name -> [total_kb, instance_count]
    for row in csv.reader(io.StringIO(result.stdout)):
        if len(row) < 5:
            continue
        kb = _parse_kb(row[4])
        if kb is None:
            continue
        entry = totals.setdefault(row[0], [0, 0])
        entry[0] += kb
        entry[1] += 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1][0], reverse=True)
    return ranked[:limit]


def sweep_lines(state):
    """Run one kill sweep (unless paused) and return report lines."""
    ts = datetime.now().strftime("%H:%M:%S")
    if state["paused"]:
        return [f"{DIM}[{ts}] paused - monitoring only{RESET}"]

    lines = [f"{DIM}[{ts}] sweep{RESET}"]
    for process in PROCESSES:
        running, dead, attempts = hammer(process)
        if not running:
            lines.append(f"  {DIM}OK      {RESET}{process} not running")
        elif dead:
            lines.append(f"  {GREEN}STOPPED {RESET}{process} "
                         f"{DIM}(after {attempts} kill(s)){RESET}")
        else:
            lines.append(f"  {RED}RESPAWNER{RESET} {process} "
                         f"{DIM}still alive after {attempts} rapid kills - retry next sweep{RESET}")
    return lines


def top_lines(limit):
    items = top_memory(limit)
    ts = datetime.now().strftime("%H:%M:%S")
    lines = [f"{CYAN}{BOLD}Top {len(items)} by memory{RESET} {DIM}[{ts}]{RESET}"]
    if not items:
        lines.append(f"  {DIM}(no data){RESET}")
        return lines
    for i, (name, (kb, count)) in enumerate(items, 1):
        lines.append(f"  {i:>2}. {GREEN}{kb / 1024:>8,.0f} MB{RESET}  "
                     f"{DIM}x{count}{RESET}  {name}")
    return lines


def target_lines():
    lines = [f"{BOLD}targets ({len(PROCESSES)}):{RESET}"]
    for process in PROCESSES:
        if is_running(process):
            lines.append(f"  {YELLOW}RUNNING {RESET}{process}")
        else:
            lines.append(f"  {DIM}absent  {RESET}{process}")
    return lines


def help_lines():
    return [
        f"{BOLD}commands:{RESET}",
        f"  {CYAN}top{RESET} / {CYAN}t{RESET}        refresh the memory list now",
        f"  {CYAN}n <count>{RESET}     show top <count> (1-40)",
        f"  {CYAN}targets{RESET}       list configured targets + live status",
        f"  {CYAN}pause{RESET} / {CYAN}resume{RESET}  stop / start the kill loop (keep monitoring)",
        f"  {CYAN}help{RESET} / {CYAN}?{RESET}        this list",
        f"  {CYAN}quit{RESET} / {CYAN}q{RESET}        stop Aegis",
    ]


def run_command(raw, state):
    """Execute a typed dev command. Returns output lines. 'quit' raises to stop."""
    parts = raw.split()
    if not parts:
        return []
    cmd = parts[0].lower()
    if cmd in ("help", "?", "h"):
        return help_lines()
    if cmd in ("top", "t"):
        return top_lines(state["top_n"])
    if cmd in ("n", "rows"):
        if len(parts) > 1 and parts[1].isdigit():
            state["top_n"] = max(1, min(40, int(parts[1])))
            return top_lines(state["top_n"])
        return [f"{YELLOW}usage: n <count>{RESET}"]
    if cmd == "pause":
        state["paused"] = True
        return [f"{YELLOW}kill loop paused (monitoring only){RESET}"]
    if cmd == "resume":
        state["paused"] = False
        return [f"{GREEN}kill loop resumed{RESET}"]
    if cmd in ("targets", "tg"):
        return target_lines()
    if cmd in ("quit", "exit", "q"):
        raise KeyboardInterrupt
    return [f"{YELLOW}unknown: {raw.strip()}  (try 'help'){RESET}"]


def _emit(lines, buf):
    """Print a block below the current prompt line, then restore the prompt + buffer."""
    text = "\n"
    if lines:
        text += "\n".join(lines) + "\n"
    text += PROMPT + buf
    sys.stdout.write(text)
    sys.stdout.flush()


def dev_console():
    """Interactive dev loop: live sweeps + memory view, with typed commands.

    Single-threaded. Each idle tick polls the keyboard (msvcrt, non-blocking);
    every CHECK_INTERVAL it runs a sweep and refreshes the memory list.
    """
    import msvcrt  # Windows stdlib; dev mode is Windows-only like the rest.

    state = {"paused": False, "top_n": 10}
    print(f"{CYAN}Dev console - live monitor every {CHECK_INTERVAL}s. "
          f"Type a command + Enter; 'help' for the list, 'quit' to stop.{RESET}")
    _emit(sweep_lines(state) + [""] + top_lines(state["top_n"]), "")

    buf = ""
    next_sweep = time.monotonic() + CHECK_INTERVAL
    while True:
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):   # arrow / function key - consume code, ignore
                msvcrt.getwch()
                continue
            if ch == "\x03":             # Ctrl+C
                raise KeyboardInterrupt
            if ch in ("\r", "\n"):       # Enter - run the buffered command
                cmd, buf = buf, ""
                _emit(run_command(cmd, state), buf)
                continue
            if ch == "\b":               # backspace
                if buf:
                    buf = buf[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            if ch == "\t":
                continue
            buf += ch                    # printable - echo it
            sys.stdout.write(ch)
            sys.stdout.flush()
            continue

        now = time.monotonic()
        if now >= next_sweep:
            _emit(sweep_lines(state) + [""] + top_lines(state["top_n"]), buf)
            next_sweep = time.monotonic() + CHECK_INTERVAL
        else:
            time.sleep(0.03)


def run_loop(dev_mode):
    if dev_mode:
        dev_console()
        return

    print(f"{GREEN}You should be safe... (its only V1){RESET} "
          f"{DIM}Leave this window open. (Ctrl+C to stop.){RESET}")

    start = time.monotonic()
    next_sweep = start
    while True:
        now = time.monotonic()
        if now >= next_sweep:
            for process in PROCESSES:
                hammer(process)
            next_sweep = now + CHECK_INTERVAL

        elapsed = int(time.monotonic() - start)
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        # \r rewrites the same line so the window never scrolls.
        sys.stdout.write(f"\r{CYAN}Aegis running{RESET} "
                         f"{BOLD}{h:02d}:{m:02d}:{s:02d}{RESET}   ")
        sys.stdout.flush()
        time.sleep(1)


def login():
    """Prompt for a login. Returns True for dev mode, False for user mode, or exits."""
    print_banner()
    entry = input(f"{BOLD}Login:{RESET} ").strip()
    if entry == DEV_LOGIN:
        clear_screen()        # remove the typed secret from view
        print_banner()
        return True
    if entry == NORMAL_LOGIN:
        return False
    print(f"{RED}Invalid login.{RESET} {DIM}Closing...{RESET}")
    time.sleep(2)             # brief pause so a typo isn't a mystery
    close_console()


def run_debug():
    """Dev-gated diagnostics, for fixing a classmate's laptop with their permission."""
    print_banner()
    entry = input(f"{BOLD}Dev secret:{RESET} ").strip()
    if entry != DEV_LOGIN:
        print(f"{RED}Access denied.{RESET}")
        sys.exit(1)

    clear_screen()            # remove the typed secret from view
    print_banner()

    obfuscated = any(m.startswith("pyarmor_runtime") for m in sys.modules)

    print(f"\n{CYAN}{BOLD}== Aegis debug =={RESET}")
    print(f"  Python version   : {platform.python_version()} "
          f"({platform.architecture()[0]})")
    print(f"  Python executable: {sys.executable}")
    print(f"  Windows          : {platform.platform()}")
    print(f"  Machine          : {platform.machine()}")
    print(f"  tasklist found   : {'yes' if shutil.which('tasklist') else 'NO'}")
    print(f"  taskkill found   : {'yes' if shutil.which('taskkill') else 'NO'}")
    print(f"  Obfuscated build : {'yes' if obfuscated else 'no (running from source)'}")
    print(f"  Check interval   : {CHECK_INTERVAL}s  |  hammer: {MAX_RETRIES} x {HAMMER_DELAY}s")

    print(f"\n  {BOLD}Targets ({len(PROCESSES)}) - live status:{RESET}")
    for process in PROCESSES:
        if is_running(process):
            print(f"    {YELLOW}RUNNING {RESET}{process}")
        else:
            print(f"    {DIM}absent  {RESET}{process}")
    print()


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "debug":
        run_debug()
        return
    dev_mode = login()
    run_loop(dev_mode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{CYAN}Aegis stopped.{RESET}")
        sys.exit(0)
