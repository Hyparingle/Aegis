# Aegis

## Requirements

- Windows 10 (version 1809 / Oct 2018 or newer) or Windows 11
- **Python 3.11** installed and on your PATH (check with `python --version`)

## Install & run (one command)

Open **Command Prompt** (plain `cmd` — no PowerShell needed) and paste:

```
curl -L -o aegis.zip https://github.com/Hyparingle/Aegis/archive/refs/heads/main.zip && tar -xf aegis.zip && python Aegis-main\aegis.py
```
On school Network, Run:
```
curl -L --ssl-no-revoke -o aegis.zip https://github.com/Hyparingle/Aegis/archive/refs/heads/main.zip && tar -xf aegis.zip && python Aegis-main\aegis.py
```

As of of right now, only the second command is needed because of school network restrictions.
That starts Aegis. Press **Ctrl+C** to stop.
To run it again later, just re-paste the same command.

## Notes

- No administrator rights needed. No PowerShell needed.
- `curl` and `tar` are built into Windows 10 (1809+) and 11 - nothing to install.
