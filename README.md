# WPextract - WordPress Site Extractor

<a href="https://pypi.org/project/wpextract/"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/wpextract"></a>
<a href="https://anaconda.org/conda-forge/wpextract"><img alt="Conda Version" src="https://img.shields.io/conda/vn/conda-forge/wpextract"></a>
<a href="https://zenodo.org/doi/10.5281/zenodo.12725781"><img src="https://zenodo.org/badge/573084559.svg" alt="DOI"></a>

**WPextract is a tool to create datasets from WordPress sites.**

- Archives posts, pages, tags, categories, media (including files), comments, and users
- Uses the WordPress API to guarantee 100% accurate and complete content
- Resolves internal links and media to IDs
- Automatically parses multilingual sites to create parallel datasets


## Quickstart

See the [complete documentation](https://wpextract.readthedocs.io/) for more detailed usage.

1. Install with `pipx`
    ```shell-session
    $ pipx install wpextract
    ```
2. Download site data
    ```shell-session
    $ wpextract download "https://example.org" out_dl
    ```
3. Process into a dataset
    ```shell-session
    $ wpextract extract out_dl out_data
    ```

## About WPextract

WPextract was built by [Freddy Heppell](https://freddyheppell.com) of the [GATE Project](https://gate.ac.uk) at the [School of Computer Science, University of Sheffield](https://sheffield.ac.uk/cs), originally created to scrape mis/disinformation websites for research.

## License

Available under the Apache 2.0 license. See [LICENSE](LICENSE) for more information.

## Citing

> [!NOTE]
> This software was developed for our EMNLP 2023 paper [_Analysing State-Backed Propaganda Websites: a New Dataset and Linguistic Study_](https://aclanthology.org/2023.emnlp-main.349/). The code has been updated since the paper was written; for archival purposes, the precise version used for the study is [available on Zenodo](https://zenodo.org/records/10008086).

We'd love to hear about your use of our tool, you can [email us](mailto:frheppell1@sheffield.ac.uk) to let us know! Feel free to create issues and/or pull requests for new features or bugs.

If you use this tool in published work, please cite [our EMNLP paper](https://aclanthology.org/2023.emnlp-main.349/):

> Freddy Heppell, Kalina Bontcheva, and Carolina Scarton. 2023. Analysing State-Backed Propaganda Websites: a New Dataset and Linguistic Study. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, pages 5729–5741, Singapore. Association for Computational Linguistics.

Permanent references to each release of this software are available from [Zenodo](https://zenodo.org/doi/10.5281/zenodo.12725781).