# Publish MarketForge AI on GitHub — Beginner Guide

Think of GitHub as a public online folder for computer projects. You are putting
a copy of the project there so other people can see it and help improve it.

## Easiest Method: GitHub Desktop

### 1. Make a GitHub account

Go to `https://github.com/` and create an account. Remember your username and
password.

### 2. Install GitHub Desktop

Go to `https://desktop.github.com/`, download GitHub Desktop and sign in with
your GitHub account.

### 3. Unzip this project

Right-click `marketforge-ai.zip`, choose **Extract All**, and place the folder
somewhere simple, for example:

```text
C:\Users\YourName\Documents\marketforge-ai
```

Do not open or upload the ZIP itself. Use the extracted folder.

### 4. Add the folder to GitHub Desktop

1. Open GitHub Desktop.
2. Click **File**.
3. Click **Add local repository**.
4. Select the extracted `marketforge-ai` folder.
5. If it says the folder is not a Git repository, click **create a repository**.
6. Keep the repository name as `marketforge-ai`.
7. Make sure **Git ignore** and **Licence** are left as **None**, because those
   files are already included.
8. Click **Create repository**.

### 5. Make the first save

GitHub calls a project save a **commit**.

1. In the bottom-left Summary box, type:
   `MarketForge AI 0.4 prospective benchmark preregistration`
2. Click **Commit to main**.

### 6. Put it online

1. Click **Publish repository** near the top.
2. Keep the name `marketforge-ai`.
3. Untick **Keep this code private** when you want everyone to see it.
4. Click **Publish repository**.

Your project is now on GitHub.


## Protect the Frozen Benchmark

Version 0.4 contains a sealed research test. Think of it like putting an exam
inside a locked envelope **before** anybody sees the questions.

The file below proves what the rules and benchmark code were before the future
market candles existed:

```text
benchmarks/frozen_v2/preregistration_lock.json
```

Publish that file with the first GitHub commit. After publishing it:

- Do not edit `benchmarks/frozen_v2/spec.json`.
- Do not edit `benchmarks/frozen_v2/model_lock.json`.
- Do not edit benchmark-related Python code for this benchmark ID.
- Do not replace the preregistration lock.
- Create a new benchmark ID when the rules or code need to change.

You can check that the seal is still valid with:

```bash
python scripts/benchmark.py preregister
python scripts/benchmark.py status
```

The future data is not ready until **3 November 2026**. Before that date, the
benchmark must remain `INCOMPLETE BY DESIGN`. That is good: it proves the scored
data did not exist when the rules were frozen.

## Very Important: GitHub Does Not Run This Python App

GitHub stores the code, like an online cupboard. GitHub Pages only runs simple
static websites and cannot run this Python forecasting server.

To make a live website, deploy the repository to a Python hosting service such
as Render. A `Dockerfile` and `render.yaml` are included for that later step.
The lightweight baseline can run on a small server. Real Kronos models need much more memory and may require paid CPU or GPU hosting. A hosted website receives uploaded files, so publish a privacy policy before inviting other people to upload data.

## How to Run It on Your Windows Computer

1. Install Python 3.10, 3.11, 3.12 or 3.13 from `https://www.python.org/downloads/`.
2. During installation, tick **Add Python to PATH**.
3. Double-click `start_windows.bat`.
4. Wait for the black window to install the project packages.
5. Your browser should open `http://127.0.0.1:7070`.

The first package installation requires an internet connection.

## How to Add the Real Kronos Model

First run MarketForge AI normally so its `.venv` folder is created. Then:

1. Install GitHub Desktop, which also installs Git.
2. Double-click `scripts\install_kronos_windows.bat`.
3. Wait while Kronos and the heavier AI packages are downloaded.
4. Restart MarketForge AI.

The first real Kronos forecast can be slow because model files must be downloaded
from Hugging Face. Start with **Kronos Mini** on an ordinary computer.

## Never Upload These Things

- Passwords
- API keys
- Exchange secret keys
- Private trading exports
- The `.venv` folder
- Downloaded model weights

The included `.gitignore` helps stop several of these from being uploaded, but
you should still check before every commit.
