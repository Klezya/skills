---
name: find-skills
description: >
  Helps discover and install agent skills from the open ecosystem.
  Trigger: When user asks "how do I do X", "find a skill for X",
  "is there a skill that can...", or wants to extend capabilities.
license: MIT
metadata:
  author: klezya
  version: "1.0"
---

## When to Use

Use this skill when the user:
- Asks "how do I do X" where X might have an existing skill
- Says "find a skill for X" or "is there a skill for X"
- Asks "can you do X" where X is a specialized capability
- Wants to search for tools, templates, or workflows
- Mentions they wish they had help with a specific domain

---

## Critical Patterns

### Pattern 1: Search Before Building

Always check if a skill exists before building from scratch.

```bash
npx skills find [query]
```

### Pattern 2: Install Globally with Auto-Confirm

```bash
npx skills add <owner/repo@skill> -g -y
```

The `-g` flag installs globally (user-level), `-y` skips confirmation.

---

## Decision Tree

```
User needs specialized capability?
  → Search: npx skills find [query]
  → Found match?  → Present to user → Offer to install
  → No match?     → Help directly with general capabilities
                   → Suggest creating own skill: npx skills init
```

---

## Common Skill Categories

| Category | Example Queries |
|----------|----------------|
| Web Development | react, nextjs, typescript, css, tailwind |
| Testing | testing, jest, playwright, e2e |
| DevOps | deploy, docker, kubernetes, ci-cd |
| Documentation | docs, readme, changelog, api-docs |
| Code Quality | review, lint, refactor, best-practices |
| Design | ui, ux, design-system, accessibility |
| Productivity | workflow, automation, git |

---

## Commands

```bash
npx skills find [query]    # Search for skills
npx skills add <package>   # Install a skill
npx skills check           # Check for updates
npx skills update          # Update all skills
npx skills init my-skill   # Create a new skill
```

---

## Resources

- **Browse skills**: https://skills.sh/
