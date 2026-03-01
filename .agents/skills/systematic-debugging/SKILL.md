---
name: systematic-debugging
description: >
  Enforces systematic root-cause debugging: investigate before fixing, trace data flow,
  single hypothesis testing, and defense-in-depth validation.
  Trigger: When encountering any bug, test failure, or unexpected behavior, before proposing fixes.
license: MIT
metadata:
  author: klezya
  version: "1.0"
---

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work

---

## Critical Patterns

### The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

### Single Hypothesis Rule

Test ONE thing at a time. Don't fix multiple things at once — you can't isolate what worked.

### 3-Fix Limit

If 3+ fixes have failed → STOP. Question the architecture, don't attempt fix #4.

---

## The Four Phases

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully** — don't skip past errors, read stack traces completely
2. **Reproduce Consistently** — can you trigger it reliably? exact steps?
3. **Check Recent Changes** — git diff, recent commits, new dependencies
4. **Gather Evidence** — in multi-component systems, add diagnostic logging at each boundary
5. **Trace Data Flow** — where does the bad value originate? See [assets/root-cause-tracing.md](assets/root-cause-tracing.md)

### Phase 2: Pattern Analysis

1. **Find Working Examples** — locate similar working code in the same codebase
2. **Compare Against References** — read reference implementation COMPLETELY, don't skim
3. **Identify Differences** — list every difference, don't assume "that can't matter"
4. **Understand Dependencies** — what components, settings, assumptions?

### Phase 3: Hypothesis and Testing

1. **Form Single Hypothesis** — "I think X is the root cause because Y"
2. **Test Minimally** — smallest possible change, one variable at a time
3. **Verify** — worked? → Phase 4. Didn't work? → new hypothesis, DON'T pile fixes

### Phase 4: Implementation

1. **Create Failing Test** — simplest reproduction, automated if possible
2. **Implement Single Fix** — address root cause, ONE change, no "while I'm here"
3. **Verify** — test passes, no regressions
4. **If 3+ fixes failed** — question architecture fundamentals, discuss before continuing

---

## Decision Tree

```
Bug reported?
  → Read error messages → Reproduce → Check recent changes
  → Multi-component? → Add diagnostic logging at each boundary → Run once
  → Traced root cause? → Find working examples → Compare
  → Form hypothesis → Test minimally → Verify
  → Fix works? → Create test → Done
  → Fix fails? → Count attempts
    → < 3? → Return to Phase 1
    → ≥ 3? → STOP → Question architecture
```

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "One more fix attempt" (when already tried 2+)

**ALL mean: STOP. Return to Phase 1.**

---

## Commands

```bash
git --no-pager diff                    # Check recent changes
git --no-pager log --oneline -20       # Recent commits
grep -rn "ERROR\|error\|Error" logs/   # Search for errors in logs
```

---

## Resources

- **Techniques**: See [assets/](assets/) for supporting techniques:
  - [root-cause-tracing.md](assets/root-cause-tracing.md) — trace bugs backward through call chain
  - [defense-in-depth.md](assets/defense-in-depth.md) — validate at every layer
  - [condition-based-waiting.md](assets/condition-based-waiting.md) — replace arbitrary timeouts
- **Tests**: See [assets/](assets/) for pressure-test scenarios
- **Creation log**: See [assets/CREATION-LOG.md](assets/CREATION-LOG.md) for extraction decisions
