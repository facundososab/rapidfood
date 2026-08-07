# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| "judgment day", "judgment-day", "review adversarial", "dual review", "doble review", "juzgar", "que lo juzguen" | judgment-day | C:/Users/renzo/.config/opencode/skills/judgment-day/SKILL.md |
| Go tests, Bubbletea TUI testing, teatest, adding test coverage | go-testing | C:/Users/renzo/.config/opencode/skills/go-testing/SKILL.md |
| Creating a GitHub issue, reporting a bug, requesting a feature | issue-creation | C:/Users/renzo/.config/opencode/skills/issue-creation/SKILL.md |
| Creating a pull request, opening a PR, preparing changes for review | branch-pr | C:/Users/renzo/.config/opencode/skills/branch-pr/SKILL.md |
| Creating a new AI skill, adding agent instructions, documenting patterns for AI | skill-creator | C:/Users/renzo/.config/opencode/skills/skill-creator/SKILL.md |
| "how do I do X", "find a skill for X", "is there a skill that can...", extending capabilities | find-skills | C:/Users/renzo/.config/opencode/skills/find-skills/SKILL.md |
| Implementing a Django module, creating/modifying a use case, adding REST endpoints, creating repositories, modifying domain logic, reviewing hexagonal architecture | django-hexagonal-modular-architecture | skills/hexagonal-architecture/SKILL.md |

> Note: SDD workflow skills, `_shared`, and `skill-registry` are intentionally omitted. The project-level `django-hexagonal-modular-architecture` skill wins for Rapidfood implementation/review work.

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### judgment-day
- Launch TWO independent blind judge sub-agents via `delegate` in PARALLEL — never sequential; orchestrator NEVER reviews code itself
- Both judges get identical target + identical criteria; neither knows about the other; always wait for BOTH before synthesizing
- Severity: CRITICAL | WARNING (real) | WARNING (theoretical) | SUGGESTION — classify warnings by "can a normal user, using the tool as intended, trigger this?"
- Synthesis: Confirmed (both) → fix immediately; Suspect (one judge) → triage, do NOT auto-fix; Contradiction → flag for manual decision
- Fix Agent is a SEPARATE delegation — never use a judge as fixer; fix only confirmed issues; if fixing a pattern in one file, fix the SAME pattern in all touched files
- After fixes → re-launch both judges in parallel; after 2 fix iterations with issues remaining → ASK the user, never auto-escalate
- APPROVED requires: Round 1 judges CLEAN, OR Round 2 with 0 CRITICAL + 0 confirmed real WARNING (theoretical warnings/suggestions may remain)
- MUST NOT commit/push or say "done" until every judgment reaches APPROVED or ESCALATED; resolve skill registry BEFORE launching judges

### go-testing
- Pure functions → table-driven tests: `tests := []struct{name, input, expected, wantErr}` + `t.Run(tt.name, ...)`
- Bubbletea TUI: test `Model.Update()` state transitions directly with `tea.KeyMsg`; full flows via `teatest.NewTestModel(t, m)`, `tm.Send(...)`, `tm.WaitFinished`, `tm.FinalModel(t)`
- Visual output → golden file testing: `testdata/*.golden`, regenerate with `go test -update ./...`
- Mock `os/exec` via interfaces; file ops use `t.TempDir()`; integration tests skip with `-short`
- Always test BOTH success and error paths (`(err != nil) != tt.wantErr`)

### issue-creation
- Blank issues are disabled — MUST use a template: `bug_report.yml` or `feature_request.yml`
- Every new issue auto-gets `status:needs-review`; a maintainer MUST add `status:approved` before any PR can be opened
- Questions go to Discussions, NOT issues; search existing issues for duplicates first
- Bug report fields: pre-flight checks, description, steps to reproduce, expected vs actual behavior, OS, agent/client, shell
- Commands: `gh issue create --template "bug_report.yml" --title "fix(scope): description"`

### branch-pr
- EVERY PR MUST link an approved issue via `Closes #N` / `Fixes #N` / `Resolves #N` — no exceptions; linked issue must have `status:approved`
- Branch names MUST match `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)/[a-z0-9._-]+$`
- Exactly ONE `type:*` label per PR (feature | bug | docs | refactor | chore | breaking-change)
- Conventional commits: `type(scope)!: description`; NO `Co-Authored-By` trailers
- PR body: linked issue, PR type, 1-3 summary bullets, file-change table, test plan, contributor checklist

### skill-creator
- Create a skill when: pattern is reused, project conventions differ from generic best practices, or complex workflow needs steps — NOT for one-off tasks or where docs already exist
- Structure: `skills/{name}/SKILL.md` (required) + optional `assets/` (templates, schemas) and `references/` (LOCAL docs only, no web URLs)
- Frontmatter required: `name` (lowercase, hyphens), `description` (what + `Trigger:`), `license` (Apache-2.0), `metadata.author`, `metadata.version`
- Content: critical patterns first, tables for decision trees, minimal code examples, Commands section; NO Keywords or troubleshooting sections
- Register the new skill in `AGENTS.md` after creating it

### find-skills
- Trigger: "how do I do X", "find a skill for X", "is there a skill for X", user wants to extend agent capabilities
- Use the Skills CLI: `npx skills find [query]`, `npx skills add <owner/repo@skill> -g -y`, `npx skills check`, `npx skills update`; browse https://skills.sh/
- Check the skills.sh leaderboard BEFORE running a CLI search (well-known skills: vercel-labs/agent-skills, anthropics/skills)
- Verify quality before recommending: 1K+ installs (skeptical under 100), official sources (vercel-labs, anthropics, microsoft), GitHub stars
- Present each option with: name + what it does, install count + source, install command, skills.sh link

### django-hexagonal-modular-architecture
- Dependency direction is ALWAYS inward: adapters → application/domain; application → port interfaces; domain → nothing external; domain must NOT import framework/ORM/web types
- Model every side effect as an outbound port (persistence, gateways, clock, logger) — ports model capabilities, not technologies
- Use cases = pure orchestration: receive ports via constructor/arguments, validate app-level invariants, return plain data structures
- Adapters at the edge: inbound converts protocol → use-case input; outbound maps app contracts → ORM/API; all mapping stays in adapters
- Composition root: single explicit wiring location; NO hidden globals, NO service locator
- Feature-first layout: `domain/`, `application/ports/{inbound,outbound}`, `application/use-cases/`, `adapters/{inbound,outbound}/`, `composition/`
- Anti-patterns: domain importing ORM/framework types, use cases reading `req`/`res`, returning DB rows directly, adapters calling each other directly
- Test per boundary: unit test use cases with fake ports, integration test adapters with real infra, E2E through inbound adapters
- Before implementation, identify the responsible bounded context, business rule, aggregate, ports, use case, adapters, container wiring, REST exposure, and tests.
- Do not add generic `shared` code unless the concept is genuinely common and justified.

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | AGENTS.md | Project index — package manager, language, Prisma ownership, architecture gate, and skill auto-invoke rules |
| Architecture guide | docs/ARCHITECTURE-GUIDE.md | Referenced by AGENTS.md; architectural source for Django shell, Prisma data layer, module boundaries |
| Domain model | docs/modelo-dominio.md | User-mandated implementation guidance source under `./docs` |
| Order state machine | docs/order-state-machine.md | User-mandated implementation guidance source under `./docs` |
| Business rules | docs/reglas-negocio.md | User-mandated implementation guidance source under `./docs` |
| Functional requirements | docs/req-funcionales.md | User-mandated implementation guidance source under `./docs` |
| Project skill | skills/hexagonal-architecture/SKILL.md | Referenced by AGENTS.md; implementation/review rules for Django hexagonal modules |

Implementation MUST be guided absolutely by `./docs` per user instruction. If docs and code disagree, surface the mismatch before implementation and prefer updating/clarifying the docs-driven spec instead of silently coding against stale assumptions.

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.
