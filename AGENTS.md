# Repository Guidelines

## Project Structure & Module Organization
This repository is a multi-service backend stack under `main/`:

- `main/xiaozhi-server`: Python core runtime (`app.py`), config in `config.yaml` and `data/.config.yaml`, plugin logic in `plugins_func/`, manual test page in `test/`.
- `main/manager-api`: Spring Boot admin API (`src/main/java`), resources in `src/main/resources`, tests in `src/test/java`.
- `main/manager-web`: Vue 2 admin console (`src/`, `public/`).
- `main/manager-mobile`: uni-app + Vue 3 mobile console (`src/`, `env/`).
- `docs/`: deployment, integration, and operations guides.

## Build, Test, and Development Commands
Run commands from each module directory:

- Python server: `cd main/xiaozhi-server && pip install -r requirements.txt && python app.py`
- API service: `cd main/manager-api && mvn spring-boot:run`
- Web console: `cd main/manager-web && npm install && npm run serve`
- Mobile console: `cd main/manager-mobile && pnpm i && pnpm dev:h5`
- Docker (server only): `cd main/xiaozhi-server && docker compose up -d`
- Docker (full stack): `cd main/xiaozhi-server && docker compose -f docker-compose_all.yml up -d`

## Coding Style & Naming Conventions
- Follow existing language conventions per module; avoid cross-module refactors in one PR.
- `manager-mobile` enforces 2-space indentation and commitlint conventional commits (`.editorconfig`, `.commitlintrc.cjs`).
- Python: use snake_case for files/functions; keep provider and plugin names descriptive (`core/providers/...`, `plugins_func/...`).
- Java: package under `xiaozhi.modules.*`; class names in PascalCase, DTO/VO/Entity suffixes preserved.
- Vue/uni-app: keep component/page names aligned with existing folder patterns in `src/`.

## Testing Guidelines
- `manager-api`: JUnit tests live in `src/test/java`; note `pom.xml` currently sets Surefire `skipTests=true`. Use `mvn -DskipTests=false test` when validating changes.
- `manager-mobile`: run `pnpm type-check` and `pnpm lint`.
- `xiaozhi-server`: use `python performance_tester.py` and `test/test_page.html` for runtime/audio validation.
- Add or update tests with behavior changes; include exact commands run in PR notes.

## Commit & Pull Request Guidelines
- Recent history follows conventional prefixes: `feat:`, `fix:`, `docs:`, `update:`, `add:`.
- Keep commits focused by module (`manager-api`, `manager-web`, etc.).
- PRs should include: change summary, affected module(s), config/env changes, verification commands, and screenshots for UI updates.
- Link related issues and document rollback or migration risk when touching config, DB changelogs, or API contracts.

## Security & Configuration Tips
- Never commit real API keys or secrets; keep them in `data/.config.yaml` (server) or `env/.env.*` (mobile/web).
- Review changes to `config.yaml`, `config_from_api.yaml`, and `application-dev.yml` carefully before merge.
