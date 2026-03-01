---
name: brainstorming
description: >
  Explores user intent, requirements and design before any creative work.
  Trigger: Before creating features, building components, adding functionality,
  or modifying behavior. MUST be used before any implementation.
license: MIT
metadata:
  author: klezya
  version: "1.0"
---

## When to Use

Use this skill when:
- Creating a new feature, component, or module
- Adding functionality or modifying behavior
- Starting any creative work that needs design decisions
- User describes an idea that needs refining

**HARD GATE**: Do NOT write code, scaffold, or implement ANYTHING until a design is presented and the user approves it. This applies to EVERY project regardless of perceived simplicity.

---

## Critical Patterns

### Pattern 1: No Implementation Without Design

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work.

### Pattern 2: One Question at a Time

Don't overwhelm with multiple questions. Ask one, wait for the answer, then ask the next. Prefer multiple choice when possible.

### Pattern 3: YAGNI Ruthlessly

Remove unnecessary features from all designs. Less scope = faster delivery = fewer bugs.

---

## Decision Tree

```
User requests creative work?
  → Check project context (files, docs, commits)
  → Ask clarifying questions (one at a time)
  → Propose 2-3 approaches with trade-offs
  → Present design section by section
  → User approves? → Save design doc → Transition to implementation
  → User rejects? → Revise and re-present
```

---

## Process

### 1. Explore Project Context
- Check files, docs, recent commits
- Understand current state before asking questions

### 2. Ask Clarifying Questions
- One question per message
- Multiple choice preferred over open-ended
- Focus on: purpose, constraints, success criteria

### 3. Propose 2-3 Approaches
- Each with trade-offs
- Lead with your recommendation and reasoning

### 4. Present Design
- Scale each section to its complexity
- Ask after each section if it looks right
- Cover: architecture, components, data flow, error handling, testing

### 5. Save Design Doc
- Write to `docs/plans/YYYY-MM-DD-<topic>-design.md`
- Commit the design document

### 6. Transition to Implementation
- Only after user approves the design

---

## Commands

```bash
# Check recent project context
git --no-pager log --oneline -10  # recent commits
ls -la                             # project structure
```

---

## Key Principles

- **One question at a time** — don't overwhelm
- **Multiple choice preferred** — easier to answer
- **YAGNI ruthlessly** — remove unnecessary features
- **Explore alternatives** — always propose 2-3 approaches
- **Incremental validation** — get approval section by section
- **Be flexible** — go back and clarify when needed
