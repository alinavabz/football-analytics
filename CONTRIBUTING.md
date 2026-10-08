# Contributing

## Workflow

1. Every change starts as a GitHub issue with acceptance criteria.
2. Work on a branch named `<type>/<issue-key>-<short-description>`, for example `feat/fba-2-raw-ingestion`.
3. Open a pull request using the template. CI must be green before merging.
4. Merge with squash so `main` has one commit per change.
5. Add an entry to `CHANGELOG.md` in the same pull request.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `test:`, `chore:`, followed by a short lowercase summary.

## Local setup

```bash
cp .env.example .env          # then set your own passwords
uv sync                       # install Python dependencies, including dev tools
uv run pre-commit install     # run lint and secret scan before every commit
make up                       # start Postgres and MongoDB
make test
```

## Make targets

| Target | What it does |
|---|---|
| `make up` | Start the stack and wait until both databases are healthy |
| `make down` | Stop and remove containers. Data volumes are kept |
| `make ps` | Show running services |
| `make test` | Run the test suite against the running stack |
| `make lint` | Check style and common errors with ruff |
| `make format` | Auto-format and fix what ruff can fix |
| `make reset` | Remove containers **and data volumes**. All data is lost |

## Secrets

Real credentials live only in `.env`, which git ignores. `.env.example` lists every variable with placeholder values. A gitleaks scan runs before each commit and in CI.
