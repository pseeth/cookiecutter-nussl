# Getting started

This guide will get you started with creating datasets for training and testing a 
deep learning based source separation model. Specifically, we will train a deep
clustering network. There are five major steps: 

1. Setting up dependencies
2. Setting all the environment variables
3. Creating the datasets
4. Setting up experiments
    - Training models
    - Evaluating models
5. Analyzing and reporting the results

This repository contains code that allows for quick and easy experimentation with the nussl library. With this code, you can easily experiment with the various hyperparameters that are native to each separation algorithm. The goal of this document is to guide you through setting up an environment via Anaconda and Docker, setting up experiment monitoring via comet.ml, setting up experiment reporting via a Google sheet, and training and testing your first model on a small dataset.

## Project organization

All commands are mainly run via the [Makefile](../Makefile), which has several useful commands that will be used throughout.

## Setting up dependencies

You'll need to first install [Docker](https://docs.docker.com/v17.12/install/) and [Anaconda](https://docs.anaconda.com/anaconda/install/). If you want GPU support, you should install nvidia-docker and CUDA on the host machine. Once you have those two, you can start setting up the environment.

### Setting up the conda environment

First, create and activate a Python 3 conda environment:

```
conda create -n [your_environment_name] python=3.7
conda activate [your_environment_name]
```


For some reason, it must be Python 3.7 due to a change in naming importlib in Python 3.8 breaking some dependencies. Then install poetry:

```
curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
```

or by writing `make poetry`. 

Then just run `make install`.

This will install all of the requirements into the conda environment.

### Setting up environment variables

The scripts are going to point to a lot of directories 
(e.g. where your data lives, where to save experiment artifacts,
and so on). They may also depend on a bunch of API keys,
like access tokens for Google sheets (optional), API keys for experiment
tracking losses and logs on comet.ml (also optional). Each environment variable
is set in `setup/environment/default.sh`. First, copy `default.sh` to something
like `[prefix]_local.sh`. It's important that the file ends in `_local.sh`. This is so that it doesn't get tracked by Git! You're putting sensitive API keys in there so be mindful!

Now edit your copied file `[prefix]_local.sh`. Below is a description of every environnment variable and how to set it.

### The environment variables


#### Required environment variables

```export DOCKER_IMAGE_NAME="user/image"```

This is the name of the Docker image that is used to run
all of the experiments. Usually it's named with your name
before the / and some identifier after (e.g. your_name/your_project).
You can optionally add a tag afterwards, like 
your_name/your_project:latest.

```export CACHE_DIRECTORY="/path/to/cache"```

The training scripts generate a cache of input/output pairs
for the network. These caches are zarr files that contain
all the input/output for the network and can be substantial
in size. It's good to know where they are so you can free up
hard drive space from time to time as needed.

```export ARTIFACTS_DIRECTORY="/path/to/artifacts"```

The experiment scripts all output their results in custom
named folders whose names are randomly generated (by comet.ml).
These folders get saved to /storage/artifacts/ inside the 
docker container. Good to know where these are so that you 
know where your results are.

```export DATA_DIRECTORY="/path/to/data"```

This folder is where all of your data lives for training and
evaluating. This folder will be mapped to /storage/data/ in your
docker container, allowing you to write the scripts in reference
to those locations. Make sure you have read/write permissions for 
the folder you are pointing to.

```export JUPYTER_HOST_PORT=8888```

Jupyter notebooks run inside a Docker container as well. The port
for the server inside the container (8888) must be forwarded to a
port on the host. Select that port here (default is 8890).
Find an open port otherwise it won't work (this is for if you are
sharing a machine).

```
export JUPYTER_PASSWORD_HASH="sha1:bed4d260d700:74cd5c1c5d43cab7e975a99c8bae5d6384d5891d"
```

You can set a password on the Jupyter server. By default, the password is `password`.
To change it, obtain the SHA hash for your chosen password. To do this, use:

```
from notebook.auth import passwd
passwd()
```

You'll be asked to put in your password twice. The SHA value will display.
Copy it (without the single quotes) and paste it below. This will be the password 
you use to login to the Jupyter server.

```export TENSORBOARD_HOST_PORT=6006```

Tensorboard can also run inside a Docker container. The port
for the server inside the container (6006) must be forwarded to a
port on the host. Select that port here (default is 8891).
Find an open port otherwise it won't work (this is for if you are
sharing a machine).

#### Optional environment variables

```export CODE_DIRECTORY=`pwd` ```

This tells the Docker container where the code containing all of
your scripts are. When the container starts, this is the folder you
will be in. You can assume relative paths from the root of this code
directory in your script. It now just uses the current working directory.

```export NUSSL_DIRECTORY="/path/to/nussl"```

This tells the Docker container where nussl is, so the scripts
can import your version of nussl. This is useful if
are editing nussl continuously and testing it. This is optional
as you could just use the version of nussl on Github. But if 
you're editing core nussl features, this is useful.

```export PATH_TO_GOOGLE_CREDENTIALS=""```

Experiment results are logged to a Google sheet. Put the path
to the Google service account credentials here. Make sure that
those credentials are not being tracked by Git. This only needs
to be visible outside the Docker (not inside the container). For 
details, see the [Google Sheets integration section](#google-sheets-integration).

```export COMET_API_KEY=""```

Put the API key you get from comet.ml after making an account here. 
comet.ml is used to monitor the experiments easily from anywhere as
they run.

### Google Sheets integration

SDR results are reported to a Google sheet for easy analysis at a glance. For more advanced analysis, you should use a Jupyter notebook or some Python scripts. To set this up, you'll need a Google sheets API key as well as a copy of the template sheet in your Drive somewhere. Here is the link to the template:

https://docs.google.com/spreadsheets/d/1NwEjBAxFLuLWBd_KzyODvhgc9Y8hB7bnVZaWfzm_T40/edit?usp=sharing

Copy this to your drive, naming the document something that you'll remember later.

Next, create Service Account Credentials via Google by following these instructions:
https://gspread.readthedocs.io/en/latest/oauth2.html. Once that's done, you'll get a JSON
file that you should save to somewhere. I put mine in `private/key.json`. Everything in
the `private` directory in this repository is not tracked by Git so it's a safe place
to put it. The JSON file will look something like:

```
{
    "private_key_id": "2cd … ba4",
    "private_key": "-----BEGIN PRIVATE KEY-----\nNrDyLw … jINQh/9\n-----END PRIVATE KEY-----\n",
    "client_email": "473000000000-yoursisdifferent@developer.gserviceaccount.com",
    "client_id": "473 … hd.apps.googleusercontent.com",
    "type": "service_account"
}
```

Go to the Google sheet you created above and share it to the email listed in the 
`client_email` field in the JSON file above. This is super important!

Finally, fill out the field titled `PATH_TO_GOOGLE_CREDENTIALS` in the `{prefix}_local.sh` file you made above. You should now have automated access to 
edit the Google sheet.





