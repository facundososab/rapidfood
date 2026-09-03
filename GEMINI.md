# Rapidfood — Agent Guidelines

## Project Overview

Rapidfood is a backend application built in Python. It exposes an HTTP shell using Django 5 and Django REST Framework (DRF), while the data layer is completely delegated to Prisma Client Python. The business logic is distributed across independent backend modules following Hexagonal Architecture.

| Component | Location | Tech Stack |
|-----------|----------|------------|
| Backend api | `api/` | Python 3.13, Django 5, DRF, Prisma Client Python, Hexagonal Architecture |
| ↳ client module | `api/modules/client/` | Client management |
| ↳ catalog module | `api/modules/catalog/` | Product catalog |
| ↳ config_coupon module | `api/modules/config_coupon/` | Coupons & configuration |
| ↳ order module | `api/modules/order/` | Order orchestration |
| ↳ conversation module | `api/modules/conversation/` | Conversational AI module |
| Frontend | `ui/` | (Currently empty) |
| Docs | `docs/` | Architecture guide |

---

## Repository Guidelines

### How to Use This Guide

Start here for cross-project norms. This is the main configuration file for AI agents working on Rapidfood.

**Component docs override this file when guidance conflicts.**
Always refer to `docs/ARCHITECTURE-GUIDE.md` for in-depth architectural decisions.

### Key Cross-Project Rules

- **Language**: All code, comments, variable names, and commit messages should be in **English**; business domain terms and UI copy may be in Spanish to match the ubiquitous language.
- **Package manager**: `uv` at the root. Dependencies are in `pyproject.toml`. Do NOT use or generate `requirements.txt`.
- **Database Rules**: Prisma (`schema.prisma`) is the absolute source of truth for the database. Django ORM is only a bridge, never the owner.
- **Hexagonal Architecture**: Dependencies flow inwards (`infrastructure -> application -> domain`).
- **Never commit secrets**: Use environment variables; `.env` files are gitignored.
- **Architecture Enforcement**: Run `import-linter` to verify cross-app boundaries and layer constraints before merging.

---

# Agent Skills

| Skill | Description | Reference |
|-------|-------------|-----------|
| `django-hexagonal-modular-architecture` | Guide for creating and modifying Django modules organized as bounded contexts. Includes strict layer rules, testing, and transactions. | [SKILL.md](skills/hexagonal-architecture/SKILL.md) |

### Auto-invoke Skills

When performing these actions, ALWAYS invoke the corresponding skill FIRST:

| Action | Skill |
|--------|-------|
| After creating/modifying a skill | `skill-sync` |
| Creating new skills | `skill-creator` |
| Regenerate AGENTS.md Auto-invoke tables (sync.sh) | `skill-sync` |
| Troubleshoot why a skill is missing from AGENTS.md auto-invoke | `skill-sync` |
