# Release Checklist

- [ ] Version updated in `app/core/config.py`, `pyproject.toml`, `CITATION.cff` and `CHANGELOG.md`
- [ ] `python -m compileall -q app tests scripts run.py`
- [ ] `ruff check . --select E,F,I,B --ignore E501,B008`
- [ ] `pytest -q --cov=app --cov-fail-under=78`
- [ ] `node --check app/static/app.js`
- [ ] Docker image builds and `/api/health` passes
- [ ] No `.env`, private data, credentials, virtual environment or model weights included
- [ ] Optional Kronos integration tested against a recorded upstream commit
- [ ] Third-party notices reviewed
- [ ] Research claims include data range, fingerprint, costs and limitations
- [ ] `python scripts/benchmark.py preregister` verifies without changing the lock
- [ ] `python scripts/benchmark.py status` reports the expected benchmark ID and seal status
- [ ] Future completed results pass `verify-results` deterministic replay before reporting
- [ ] Prospective benchmark status is reported as incomplete before the collection date
- [ ] `preregistration_lock.json` is committed before the scored holdout begins
- [ ] Any benchmark-code change uses a new benchmark ID instead of replacing the lock
- [ ] Git tag and GitHub release notes created
