# Copilot Skills Registry

This repository is the centralized source of personal skills for GitHub Copilot CLI.

**Install skills with symlinks:**
```bash
./install.sh --global                           # All skills → ~/.agents/skills/
./install.sh --target /path/to/project s1 s2    # Specific skills → project
./install.sh --list                             # List available skills
```

---

## 🔍 Discovery & Research

| Skill | Trigger | Link |
|-------|---------|------|
| `find-skills` | "find a skill for...", "is there a skill that..." | [SKILL.md](.agents/skills/find-skills/SKILL.md) |

---

## 🐛 Debugging

| Skill | Trigger | Link |
|-------|---------|------|
| `systematic-debugging` | Any bug, test failure, or unexpected behavior | [SKILL.md](.agents/skills/systematic-debugging/SKILL.md) |

---

## 🏗️ Design & Planning

| Skill | Trigger | Link |
|-------|---------|------|
| `brainstorming` | Before creating features, components, or new functionality | [SKILL.md](.agents/skills/brainstorming/SKILL.md) |

---

## 🛠️ Code Quality

| Skill | Trigger | Link |
|-------|---------|------|
| `fastapi-best-practices` | Creating or modifying FastAPI endpoints, services, or routers | [SKILL.md](.agents/skills/fastapi-best-practices/SKILL.md) |

---

## 🔒 Security

| Skill | Trigger | Link |
|-------|---------|------|
| `web-security` | Hardening a web API, reviewing security, OWASP compliance | [SKILL.md](.agents/skills/web-security/SKILL.md) |

---

## 🚀 Deployment

| Skill | Trigger | Link |
|-------|---------|------|
| `production-deployment` | Deploying, containerizing, configuring nginx/Docker/TLS | [SKILL.md](.agents/skills/production-deployment/SKILL.md) |

---

## 🧩 Tooling & Workflow

| Skill | Trigger | Link |
|-------|---------|------|
| `skill-creator` | "create a skill", "add agent instructions", or documenting patterns for AI | [SKILL.md](.agents/skills/skill-creator/SKILL.md) |
| `session-logger` | Start/end of session, after file changes, "update session", "what were we doing" | [SKILL.md](.agents/skills/session-logger/SKILL.md) |

---

## Adding a New Skill

1. Create `.agents/skills/{skill-name}/SKILL.md` following the [skill-creator](.agents/skills/skill-creator/SKILL.md) guidelines
2. Register it in the table above
3. Run `./install.sh --global` to symlink globally, or `./install.sh --target /path` for a specific project
