# Project conventions

- Language: all code, commits, branches, and identifiers (classes, functions, variables) are written in English, even though we converse in Portuguese. End-user-facing CLI/API output strings may stay in Portuguese.
- Dependencies: managed via `pyproject.toml`, never `requirements.txt`.
- Comments/docstrings: none by default. Only comment when something is genuinely non-obvious from reading the code.
- Structure: separate code by responsibility — one concern per module (e.g. browser automation, HTML parsing, CLI/orchestration each in their own file).
- Async: prefer async APIs over sync (e.g. `patchright.async_api`) for I/O-bound code such as browser automation.
- Tests: always write unit tests for new functionality as it's built, using `pytest`.

# Architecture

Three components, built in this order:
1. **bot** — Patchright (Chromium) automation of the Receita Federal public CPF lookup form (hCaptcha-protected). Captcha resolution is pluggable.
2. **solver** — resolves the hCaptcha challenge on the bot's page.
3. **api** — orchestrates bot + solver behind a service interface (sync client-facing, async internally toward bot/solver).
