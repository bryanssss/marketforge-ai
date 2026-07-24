# Upgrade Patch: MarketForge AI 0.4.3 to 0.5.0

1. Back up your current repository and local `storage/marketforge.db`.
2. Copy every file and folder from this patch into the root of your local `marketforge-ai` repository.
3. Choose **Replace files in the destination** when asked.
4. Do not add your local database, `.venv`, model weights or private datasets to Git.
5. Commit with: `Release MarketForge AI 0.5 research workbench`.
6. Push and wait for the newest GitHub Actions to pass.
7. Create prerelease tag `v0.5.0`.

The official prospective protocol is now `benchmarks/frozen_v3`. Versions 1 and 2 remain historical records.
