# Publish MarketForge AI 0.5 on GitHub — Beginner Guide

Think of GitHub as a public online folder that remembers every saved version of a
software project.

## Updating an Existing MarketForge Repository

If `marketforge-ai` is already connected to GitHub Desktop:

1. Download and extract the MarketForge AI 0.5 release ZIP.
2. Open the extracted folder and copy all project files.
3. Open your existing local `marketforge-ai` repository folder.
4. Paste the files and choose **Replace files in the destination**.
5. Do not copy `.venv`, `storage/marketforge.db`, downloaded model weights or private data.
6. Open GitHub Desktop and review the changed-file list.
7. Use this commit message:

```text
Release MarketForge AI 0.5 research workbench
```

8. Click **Commit to main** and then **Push origin**.
9. Open GitHub Actions and wait for the newest Quality checks, CodeQL and benchmark
   smoke checks.
10. Create a `v0.5.0` prerelease only after the newest checks are green.

## Publishing a New Repository

### 1. Create a GitHub Account

Create an account at `https://github.com/`.

### 2. Install GitHub Desktop

Download GitHub Desktop from `https://desktop.github.com/` and sign in.

### 3. Extract the Project

Right-click the release ZIP, choose **Extract All**, and place the folder somewhere
simple, for example:

```text
C:\Users\YourName\Documents\marketforge-ai
```

Do not upload only the ZIP. GitHub should contain the files and folders inside it.

### 4. Add It to GitHub Desktop

1. Open GitHub Desktop.
2. Click **File → Add local repository**.
3. Select the extracted `marketforge-ai` folder.
4. When asked, create a repository in that folder.
5. Keep the name `marketforge-ai`.
6. Leave Git ignore and Licence as **None** because the project already includes them.

### 5. Create the First Commit

Use:

```text
MarketForge AI 0.5 prospective v3 preregistration
```

Click **Commit to main**.

### 6. Publish It

1. Click **Publish repository**.
2. Untick **Keep this code private** when the preregistration must be publicly verifiable.
3. Click **Publish repository**.

## Protect the Official Frozen Benchmark

MarketForge AI 0.5 contains the official prospective v3 protocol. Think of it as a
sealed exam prepared before the future market candles exist.

The public proof file is:

```text
benchmarks/frozen_v3/preregistration_lock.json
```

After publishing it:

- do not edit `benchmarks/frozen_v3/spec.json`;
- do not edit `benchmarks/frozen_v3/model_lock.json`;
- do not replace the preregistration lock;
- do not change benchmark-bound code under the same identifier;
- create `frozen_v4` when a later methodology needs to change.

Verify the seal with:

```bash
python scripts/benchmark.py preregister
python scripts/benchmark.py status
```

Before 3 November 2026, the correct status is:

```text
PREREGISTERED — INCOMPLETE BY DESIGN
```

Versions 1 and 2 remain historical audit records. Do not delete or rewrite them.

## Files That Must Never Be Published

- `.env`
- API keys or passwords
- exchange secret keys
- wallet secrets
- private trading exports
- confidential datasets
- `.venv`
- `storage/marketforge.db`
- downloaded Kronos weights
- `vendor/Kronos`
- generated frozen benchmark results that have not been reviewed

The included `.gitignore` blocks common local files, but always review GitHub Desktop's
changed-file list before committing.

## GitHub Does Not Run the Python Server

GitHub stores the source code. GitHub Pages cannot run this FastAPI application.

Run it locally with:

```text
start_windows.bat
```

or:

```bash
./start_mac_linux.sh
```

A hosted deployment requires a Python service or container host. Hosted processing is
not local processing: uploaded files reach the server operator.

## Create the v0.5.0 Release

After the newest Actions are green:

1. Open **Releases → Create a new release**.
2. Create tag `v0.5.0` from the newest green `main` commit.
3. Use title:

```text
MarketForge AI 0.5.0 — Research Workbench and Prospective Benchmark v3
```

4. Mark it as a prerelease.
5. Attach the audited ZIP and its `.sha256` file.
6. State clearly that the prospective benchmark is incomplete and no superiority claim
   currently exists.
