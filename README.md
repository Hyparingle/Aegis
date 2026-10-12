# Aegis

A small Windows tool that frees up resources by repeatedly stopping known
bloatware processes. Runs in your Command Prompt window until you close it.

## Requirements

- Windows 10 (version 1809 / Oct 2018 or newer) or Windows 11
- **Python 3.11** installed and on your PATH (check with `python --version`)

> If you're on a different Python version and Aegis won't start, let me know your
> version and I'll send a matching build.

## Install & run (one command)

Open **Command Prompt** (plain `cmd` — no PowerShell needed) and paste:

```
curl -L -o aegis.zip https://github.com/Hyparingle/Aegis/archive/refs/heads/main.zip && tar -xf aegis.zip && python Aegis-main\aegis.py
```

That downloads Aegis, unpacks it, and starts it. Press **Ctrl+C** to stop.
To run it again later, just re-paste the same command (or run `python Aegis-main\aegis.py`).

## Notes

- No administrator rights needed. No PowerShell needed.
- `curl` and `tar` are built into Windows 10 (1809+) and 11 - nothing to install.
- The code is obfuscated; you don't need to (and can't easily) edit it.
