# Copilot Skills Registry

This repository contains personal skills for GitHub Copilot CLI.
Install any skill with: `copilot /skills install <skill-name>`

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

## 🧩 Tooling & Workflow

| Skill | Trigger | Link |
|-------|---------|------|
| `skill-creator` | "create a skill", "add agent instructions", or documenting patterns for AI | [SKILL.md](.agents/skills/skill-creator/SKILL.md) |
| `session-logger` | Start/end of session, after file changes, "update session", "what were we doing" | [SKILL.md](.agents/skills/session-logger/SKILL.md) |

---

## Adding a New Skill

1. Run `copilot /skills` and follow the prompts, or
2. Manually create `.agents/skills/{skill-name}/SKILL.md` following the [skill-creator](..agents/skills/skill-creator/SKILL.md) guidelines
3. Register it in the table above
