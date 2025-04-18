# Development

## Environment setup

Development environment is setup using [python-poetry](https://python-poetry.org/) package manager


```bash
# create virtual environment and install all dev dependencies
poetry install -E dashboard
# install git hooks (pre-commit)
poetry run pre-commit install
```

Translations are managed by using [`gettext`](https://www.gnu.org/software/gettext/manual/html_node/) that must be installed on system to manage translations. Typically, on Ubuntu:

```bash
sudo apt-get update
sudo apt install gettext
```
