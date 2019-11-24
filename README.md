# Cookiecutter for NUSSL experiments

Cookiecutter for NUSSL
====================

A boilerplate for reproducible and transparent computer audition research that leverages
the NUSSL library, which is primarily used for source separation. This project uses
[cookiecutter](https://cookiecutter.readthedocs.io/en/latest/readme.html).
*A logical, reasonably standardized, but flexible project structure for doing and 
sharing data science work.*

Requirements
------------
Install `cookiecutter` command line: `pip install cookiecutter`    

Usage
-----
To start a new science project:

`cookiecutter gh:pseeth/cookiecutter-nussl`

Project Structure
-----------------

```
.
├── cookiecutter_repo
│   ├── algorithms
│   │   ├── __init__.py
│   ├── dataset
│   │   ├── __init__.py
│   │   └── scaper_mixer.py
│   ├── __init__.py
│   ├── model
│   │   ├── __init__.py
│   ├── test
│   ├── train
│   │   └── __init__.py
│   └── utils
│       ├── __init__.py
│       ├── parallel.py
├── data_prep
│   ├── incoherent.yml
│   └── resample.yml
├── Dockerfile
├── experiments
│   └── train.yml
├── Makefile
├── notebooks
│   └── yaml.ipynb
├── poetry.lock
├── pyproject.toml
├── requirements.txt
├── runners
│   ├── config.py
│   ├── docker_runner.py
│   ├── experiment_runner_pool.py
│   ├── experiment_runner.py
│   ├── __init__.py
│   └── utils.py
├── scripts
│   ├── data.py
│   ├── prepare_urbansound.py
│   ├── resample.py
│   └── run_in_docker.py
├── setup
│   ├── build_docker_image.sh
│   ├── environment
│   │   ├── cortex_local.sh
│   │   ├── default.sh
│   │   └── gpubox_local.sh
│   ├── install_docker.sh
│   └── melodia
│       ├── MELODIA - License.txt
│       ├── mtg-melodia.cat
│       ├── mtg-melodia.n3
│       ├── mtg-melodia.so
│       └── README_linux64.txt
└── tests
```

License
-------
This project is licensed under the terms of the [MIT License](/LICENSE)