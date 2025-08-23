# Cleanup & Maintainability Checklist (Python)

> Use this file as the _post-feature_ cleanup phase. Run it in a single non-interactive session.
> Goal: keep the codebase tidy, typed, tested, documented, and dependency-hygienic.

---

## 0 Scope & Guardrails

- [ ] **No behavior changes** unless explicitly noted.
- [ ] Keep diffs small, atomic; separate refactors from functional changes.
- [ ] Never print secrets; never commit `.env` or credentials.
- [ ] If any step would introduce risk, open a separate PR instead.

---

## 1 Environment & Tooling

- [ ] Confirm Python version support (e.g., `3.11+`) and set `python_requires` in `pyproject.toml` / `setup.cfg`.
- [ ] Use an isolated env (`venv`, `poetry`, or `uv`). Document the choice in README.
- [ ] Ensure local install works:
  - `pip install -e .[dev]` **or** `poetry install` **or** `uv pip install -e .[dev]`.

---

## 2 Formatting, Linting, Types

- [ ] **Format** with `black` (or chosen formatter). Commit changes.
- [ ] **Lint** with `ruff` (or `flake8`) and fix violations.
- [ ] **Type check** with `mypy` (or `pyright`) and resolve all errors.
- [ ] Tighten config:
  - `pyproject.toml` / `ruff.toml` / `mypy.ini`: enable strict-but-reasonable rules.
  - No blanket `# noqa` or `type: ignore` without justification.

**Suggested commands**

```bash
black .
ruff check . --fix
mypy .
```
