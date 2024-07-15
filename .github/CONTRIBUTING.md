# Contributing to WPextract

We welcome contributions to WPextract! Here's some helpful guidelines.

## Get Started

To install WPextract for development, you'll need [Poetry](https://python-poetry.org/) to automatically manage the virtual environment.

Fork and clone the repo, then run `poetry install` (or `poetry install --with docs` if you'd like to build the documentation locally). This will install all the dependencies and the package itself as an editable install.

It's best practice to make an issue before a PR so any necessary discussions can be had. 

## Testing

Tests for WPextract are written with pytest. Some tips for writing tests:

* approximately follow the module structure in the tests directory
* use [pytest-datadir](https://pypi.org/project/pytest-datadir/) to handle disk usage
* make sure to properly mock parts of the code which make HTTP requests (see tests of the `download` module for help)

To run tests, use:

```shell-session
# Just run tests
$ make testonly 
# Run tests and open coverage HTML
$ make test
```

## Linting

We use [Ruff](https://docs.astral.sh/ruff/) to lint WPextract. This happens in two stages, which can be easily run with Make tasks:

```shell-session
# Reformat code
$ make format
# Find problems, autofixing if possible
$ make lint
``` 

Both library code and tests are linted (although tests are slightly less restrictive, see `pyproject.toml`).

## Branch Management

Generally your contribution should be made to the `dev` branch. We will then merge it into `main` only when it's time to release.

The exception to this is for documentation, where changes should be applied directly to `main` if they are corrections of the current documentation version (but still `dev` if they relate to upcoming changes).

## Documentation

Documentation for WPextract is built with Mkdocs and Read the Docs.

To build documentation locally (ensuring that the project was installed with the `--with docs` flag), run:

```shell-session
$ make docdev
```

When a PR is created, Read the Docs will build a preview version. If this isn't left as a comment on the PR, check [the dashboard here](https://readthedocs.org/projects/wpextract/builds/).

Documentation is hosted at:

- The [latest](https://wpextract.readthedocs.io/en/latest/) version is built from `main`
- The [unstable next release](https://wpextract.readthedocs.io/en/dev/) is built from `dev`

We use the `latest` version built from `main` as the public documentation, as this allows fixes to the live docs to be made without having to create a new release.  

The following parts of the documentation may require manual updates along with your changes:

- the API reference documents a manually-selected set of classes, which cover the two high-level functionality classes and any necessary classes (or types) required to use them.
- the CLI usage docs are manually written, generally copying the help messages but sometimes more detailed.
- if changing the LangPicker base class, the examples of how to write language pickers [here](https://wpextract.readthedocs.io/en/latest/advanced/multilingual/).

## Releasing

To make a new release, we merge `dev` to `main` the tag the commit. This automatically triggers a workflow to publish to PyPI. After a while, the [conda-forge feedstock](https://github.com/conda-forge/wpextract-feedstock) will automatically receive a PR to update the version.