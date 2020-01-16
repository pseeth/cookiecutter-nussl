#!/usr/bin/env bash
# [wf] set up environment

# USAGE
# This file should be copied to a local file called 
# {prefix}_local.sh which will not be tracked by
# git. Run that file to set up your environment so everything
# works.

# This is the name of the Docker image that is used to run
# all of the experiments. Usually it's named with your name
# before the / and some identifier after (e.g. your_name/your_project).
# You can optionally add a tag afterwards, like 
# your_name/your_project:latest.
export DOCKER_IMAGE_NAME="{{ cookiecutter.DOCKER_IMAGE_NAME }}"

# This sets up all of the paths you need on the host machine. 
# The data in those folders gets mounted inside the container,
# which is then used by the scripts to train or test a separation
# algorithm.

# The training scripts generate a cache of input/output pairs
# for the network. These caches are zarr files that contain
# all the input/output for the network and can be substantial
# in size. It's good to know where they are so you can free up
# hard drive space from time to time as needed.
export CACHE_DIRECTORY="{{ cookiecutter.CACHE_DIRECTORY }}"

# The experiment scripts all output their results in custom
# named folders whose names are randomly generated (by comet.ml).
# These folders get saved to /storage/artifacts/ inside the 
# docker container. Good to know where these are so that you 
# know where your results are.
export ARTIFACTS_DIRECTORY="{{ cookiecutter.ARTIFACTS_DIRECTORY }}"

# This folder is where all of your data lives for training and
# evaluating. This folder will be mapped to /storage/data/ in your
# docker container, allowing you to write the scripts in reference
# to those locations. Make sure you have read/write permissions for 
# the folder you are pointing to.
export DATA_DIRECTORY="{{ cookiecutter.DATA_DIRECTORY }}"

# Jupyter notebooks run inside a Docker container as well. The port
# for the server inside the container (8888) must be forwarded to a
# port on the host. Select that port here (default is 8890).
export JUPYTER_HOST_PORT={{ cookiecutter.JUPYTER_HOST_PORT }}

# Tensorboard can also run inside a Docker container. The port
# for the server inside the container (6006) must be forwarded to a
# port on the host. Select that port here (default is 8891).
export TENSORBOARD_HOST_PORT={{ cookiecutter.TENSORBOARD_HOST_PORT }}

# Obtain the SHA hash for your chosen password and copy it below. To do this, use:
# from notebook.auth import passwd
# passwd()
# You'll be asked to put in your password twice. The SHA value will display.
# Copy it (without the single quotes) and paste it below. This will be the password 
# you use to login to the Jupyter server.
# By default the password is 'password'
export JUPYTER_PASSWORD_HASH="{{ cookiecutter.JUPYTER_PASSWORD_HASH }}"

# This tells the Docker container where the code containing all of
# your scripts are. When the container starts, this is the folder you
# will be in. You can assume relative paths from the root of this code
# directory in your script. It now just uses the current working directory.
export CODE_DIRECTORY=`pwd`

# # This tells the Docker container where nussl is, so the scripts
# # can import your version of nussl. This is useful if
# # are editing nussl continuously and testing it. This is optional
# # as you could just use the version of nussl on Github. But if 
# # you're editing core nussl features, this is useful.

# export NUSSL_DIRECTORY="path/to/nussl"

# Experiment results are logged to a Google sheet. Put the path
# to the Google service account credentials here. Make sure that
# those credentials are not being tracked by Git. This only needs
# to be visible outside the Docker (not inside the container).
export PATH_TO_GOOGLE_CREDENTIALS="{{ cookiecutter.PATH_TO_GOOGLE_CREDENTIALS }}"

# Put the API key you get from comet.ml after making an account here. 
# comet.ml is used to monitor the experiments easily from anywhere as
# they run.
export COMET_API_KEY="{{ cookiecutter.COMET_API_KEY }}"