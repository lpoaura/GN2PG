# Packaging and deployment

# Packaging

This plugin is using the [python-poetry](https://python-poetry.org/) tool to perform packaging operations.

Under the hood, the package command is performing a `git archive` run based on `CHANGELOG.md` and git tags.


# Release a version

Through git workflow:

1. Add the new version to the `CHANGELOG.md`
1. Change the version number in `pyproject.toml` and `gn2pg/metadata.py`
1. Apply a git tag with the relevant version: `git tag -a X.y.z {git commit hash} -m "This version rocks!"`
1. Push tag to `main` branch: `git push origin X.y.z`
