Introduction
====================

A boilerplate for reproducible and transparent computer audition research that leverages
[nussl](https://interactiveaudiolab.github.io/nussl/), a source separation library. This 
project provides boilerplate code for training neural network models to separate mixtures
containing multiple speakers, music, and environmental sounds. It is easy to add and
train new models or datasets (GPU sold separately). The goal of this project is to enable
further reproducibility within the source separation community.

Usage
-----
To start a new project:

`cookiecutter gh:pseeth/cookiecutter-nussl` 

<!-- **TODO: Make this nussl/cookiecutter*-->

Documentation
-------------

The documentation is [here](https://pseeth.github.io/cookiecutter-nussl/). It includes
guides for getting started, training models, creating datasets, and API documentation.

Features
------------

The following models can be trained:

- Mask Inference
- Deep Clustering
- Chimera
- TasNet

on the following datasets:

- MUSDB18
- MIR-1k
- Slakh
- WSJ0-mix2
- Wham!

This project utilizes building block components from `nussl` for input/output 
(reading/writing audio, STFT/iSTFT, masking, etc.), and for neural network construction
(recurrent networks, convolutional networks, etc) to train models with minimal setup.
The main source separation library, `nussl`, contains many pre-trained models trained
using this code. See the [External File Zoo (EFZ)](http://nussl.ci.northwestern.edu/)
for

This project uses
[cookiecutter](https://cookiecutter.readthedocs.io/en/latest/readme.html).
Cookiecutter is a *logical, reasonably standardized, but flexible project structure
for doing and sharing research.* This project and `nussl` are both built upon
the [PyTorch](https://pytorch.org/) machine learning framework, as such, building new
components is as simple as adding new PyTorch code, though writing python is not required.

Requirements
------------
- Install `cookiecutter` command line: `pip install cookiecutter` (generates boilerplate 
code)
- Install [Anaconda or Miniconda](https://www.anaconda.com/distribution/)
- Install [Docker](https://www.docker.com/) and [NVIDIA Docker](https://github.com/NVIDIA/nvidia-docker)
- Install Poetry: https://poetry.eustace.io/docs/#installation (dependency management)

Guiding Principles
-----------------
The idea behind this project structure is to make it easy to use `nussl` to set up
source separation experiments. The functionality here is such that classes are taken
from `nussl` and can be extended and customized by your package code. For example, to
set up a new type of training scheme, you might subclass the Trainer class from 
`nussl` and then modify it by overriding functions from the original Trainer class
with your own implementation.

If you're trying new types of models, you can use the existing SeparationModel class but
add custom modules in `model/extras/`. These extra modules are handed to 
SeparationModel so it can resolve the model configuration. Note that models trained using
extra modules will need to be shipped with the accompanying code to be portable. For a new
model architecture to be shipped via nussl's external file zoo, the accompanying modules
must be pull requested to the main nussl repository and then deployed.

If you are implementing new separation algorithms, you can work in the `algorithms/`
folder. Implement your algorithm and then include it in `algorithms/__init__.py`. The 
base classes in nussl for all separation algorithms are included already: `SeparationBase`,
`MaskSeparationBase`, and `ClusteringSeparationBase`. 
Your new algorithm will now be accessible by the scripts via `.yml` files. Once your new
algorithm is implemented to your satisfaction, you can factor it out of the cookiecutter
and start a PR for nussl to contribute it to the main library.

All scripts, which are kept in the `scripts/` folder should take in a `.yml` file and 
function according to the parsed `.yml` file. This is to make sure every part of the
pipeline you create in your experiment is easily reproducible by processing a sequence
of `.yml` files with their associated scripts. This prevents "magic commands" with
mysterious and long forgotten command-line arguments that you ran one time 3 months ago 
from occurring. 

License
-------
This project is licensed under the terms of the [MIT License](/LICENSE)