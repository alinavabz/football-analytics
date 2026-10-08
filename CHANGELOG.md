# Changelog

All notable changes to this project are recorded here. Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Docker Compose stack with PostgreSQL 16 and MongoDB 7, credentials read from `.env`, health checks on both services.
- Smoke tests that connect to each database and confirm it answers.
- Makefile targets for the local workflow.
- Pre-commit hooks: whitespace and YAML checks, ruff lint and format, gitleaks secret scan.
- CI on every pull request: lint, full-history secret scan, and tests against the Compose stack.
- Pull request and issue templates, contributing guide.
