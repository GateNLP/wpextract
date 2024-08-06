# Installing

WPextract is available on the PyPI and Anaconda package indexes.

The minimum supported Python version is 3.9. WPextract should work on any Python-supported operating system.

## With `pipx` (recommended for end-users)

[pipx](https://pipx.pypa.io/stable/) will automatically install WPextract and its dependencies in an isolated yet globally-accessible environment.

We recommend this method for those wishing to use WPextract through its command line interface.

1. If pipx is not already installed, follow the steps in the [pipx installation instructions](https://pipx.pypa.io/stable/installation/)
2. Install WPextract:
    ```shell-session
    $ pipx install wpextract
    ```
3. Test installation:
    ```shell-session
    $ wpextract --help
    ```

??? info "Upgrading"

    To upgrade versions use:
    ```shell-session
    $ pipx upgrade wpextract
    ```
??? info "Multiple/Specific Versions"
    To install a specific version, use:
    ```shell-session
    $ pipx install wpextract==1.0.0
    ```
    Multiple versions can be installed in parallel using suffixes:
    ```shell-session
    $ pipx install --suffix=@1.0.0 wpextract==1.0.0
    $ pipx install --suffix=@1.1.0 wpextract==1.1.0
    $ wpextract@1.0.0 --version
    $ wpextract@1.1.0 --version
    ```
    The suffix is user-specified and does not necessarily have to match the version number.

??? info "Uninstalling"
    To uninstall, use:
    ```shell-session
    $ pipx uninstall wpextract
    ```
    This will cleanly uninstall the package and delete its environment


## With `pip` or `conda`

To install within an existing environment, which is necessary to use WPextract as a library.

WPextract can be manually installed with:

=== "Pip"
    ```shell-session
    $ pip install wpextract
    ```
=== "Conda"
    ```shell-session
    $ conda install wpextract
    ```

The installation can be tested through the command-line interface:

```shell-session
$ wpextract --help
```

or through importing as a library:

```pycon
>>> import wpextract
>>> wpextract.__version__
1.0.0
```

## For Development

Dependencies for development and packaging are managed through [Poetry](https://python-poetry.org/).

Poetry will automatically install dependencies and the package itself in editable mode:

 ```shell-session
 $ poetry install
 $ poetry install --with docs # to build docs locally
 $ wpextract --help
 ```
