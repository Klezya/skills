---
name: session-logger
description: "Maintains a daily session log (sessions/YYYY-MM-DD.md) per project recording objectives, changed files, and summaries to help Copilot CLI resume context across sessions. Trigger: At the start of any session, after any file change, or when user says 'update session','log this', 'end session', or 'what were we doing'."
---

## When to Use

- **Start of session**: Read `sessions/YYYY-MM-DD.md` (today) or latest existing file to restore context
- **After any file edit or creation**: Append the changed file + one-line summary of what changed
- **After completing a task or feature**: Update the objective/progress section
- **End of session / end of chat**: Add "Pending" section with next steps
- **User asks "what were we doing" or "resume"**: Read latest session file and summarize

---

## Critical Patterns

### 1. File location
```
{project-root}/sessions/YYYY-MM-DD.md
```
- One file per calendar day
- If file doesn't exist yet, create it with the template from [assets/session-template.md](assets/session-template.md)

### 2. Never overwrite — always append or update in-place
- Changes go under `## Changes` — one `### filename` subsection per file
- If the file already has a subsection for that file, append to it, don't duplicate
- Keep summaries to 1-3 bullet points per file

### 3. Ask before writing if scope is wide
If a single session touches more than 8 files or spans multiple unrelated features, ask:
> "El scope es amplio. ¿Quieres que divida el log por feature o hago un resumen global?"

### 4. Pending section at end of chat
Always close the session with:
```markdown
## Pendiente para mañana
- [ ] {next actionable task}
```

---

## Session File Structure

```markdown
# Session YYYY-MM-DD

## Objetivo
{One sentence: what was the goal of this session}

## Contexto activo
- Rama: `{branch}`
- Stack: {technologies}
- Proyecto: {project name or path}

## Cambios
### `{path/to/file}` — [NUEVO | MODIFICADO | ELIMINADO]
- {What changed and why, 1-3 bullets}

## Resumen
{2-3 sentences of what was accomplished}

## Pendiente para mañana
- [ ] {task 1}
- [ ] {task 2}
```

---

## Decision Tree

```
Session start?
  → File exists today?  → Read + summarize context for user
  → No file today?      → Check latest file → summarize, then create today's file

File was changed?
  → Add/update subsection under ## Cambios

Task completed?
  → Update ## Objetivo and ## Resumen

Chat ending?
  → Write ## Pendiente para mañana
  → Write ## Resumen if missing

User asks "what were we doing"?
  → Read latest session file → respond with context summary
```

---

## Commands

```bash
# View today's session
cat sessions/$(date +%Y-%m-%d).md

# View latest session (any day)
ls sessions/ | sort | tail -1 | xargs -I{} cat sessions/{}

# List all sessions
ls -la sessions/

# Add sessions/ to .gitignore (if desired)
echo "sessions/" >> .gitignore
```

---

## Resources

- **Template**: See [assets/session-template.md](assets/session-template.md) for the starter file
- **Gitignore snippet**: See [assets/gitignore.snippet](assets/gitignore.snippet)
