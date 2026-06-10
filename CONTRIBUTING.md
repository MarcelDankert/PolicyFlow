# Contributing

PolicyFlow is governed work. Contributions should keep workflow state, evidence,
tests, and pull request claims aligned.

## Development Setup

```bash
python -m pip install -e .[dev]
pytest -q
```

## Workflow-First Contributions

Before implementation starts:

1. create or update a workflow under `workflows/features/`
2. lock scope, non-goals, risk, required reviews, and evidence expectations
3. keep implementation changes inside the declared scope
4. update matching docs, tests, packaged assets, and examples when the public
   contract changes

## Pull Request Expectations

Every pull request should:

- reference the linked issue
- reference the governing workflow file
- include risk, confidence, evidence, and override claims
- list validation commands that were actually run
- keep generated or local-only artifacts out of git

Use the repository pull request template and run the narrowest relevant tests
before broader checks.

## Reporting Issues

Use GitHub issues for bugs, documentation gaps, and productization work. Include
the affected command, workflow file, expected behavior, actual behavior, and the
smallest reproduction path you can provide.
