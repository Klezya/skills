# [PROJECT NAME] — Agent Context

> Copy this file to your project root as `AGENTS.md` and fill in the sections below.
> Copilot CLI reads this file automatically at the start of each session.

---

## Project Context

- **Description**: [What this project does in 1-2 sentences]
- **Stack**: [e.g. FastAPI + SQLModel + PostgreSQL + React]
- **Repo**: [GitHub URL]
- **Main branch**: `main` / `develop`

## Architecture

```
[project-root]/
├── [src/]         # [description]
├── [tests/]       # [description]
├── [docs/]        # [description]
└── ...
```

**Key conventions**:
- [e.g. "Services are in src/{domain}/service.py"]
- [e.g. "All endpoints must be async"]
- [e.g. "Use SQLModel for all DB models"]

---

## Active Skills

Install with `copilot /skills install <skill-name>`

| Skill | Purpose in this project |
|-------|------------------------|
| `session-logger` | Track daily changes and resume context |
| `systematic-debugging` | Debug failures before proposing fixes |
| `brainstorming` | Design features before implementing |
| [add more as needed] | |

---

## Session Logs

Daily session logs live in `sessions/YYYY-MM-DD.md`.
- Copilot reads the latest log at session start to restore context
- Copilot updates the log after each significant change
- Add `sessions/` to `.gitignore` if logs are local-only

---

## Important Files

| File | Purpose |
|------|---------|
| [e.g. `src/config.py`] | [App configuration and env vars] |
| [e.g. `src/database.py`] | [DB session and connection] |
| [add more] | |

---

## Known Constraints

- [e.g. "Python 3.11+ only"]
- [e.g. "No synchronous DB calls inside async endpoints"]
- [e.g. "All PRs require passing tests on CI"]
