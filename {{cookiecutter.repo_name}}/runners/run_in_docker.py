from . import DockerRunner
from argparse import ArgumentParser
import subprocess
import os

def run_in_docker():
    """
    Runs a command in a Docker container. Can be configured to name the container and
    give it GPUs. The configuration of the docker is controlled in :py:mod:`runners.config`.

    For example:

    .. code-block:: bash

       # Runs a Docker container with two GPUs.
       python -m runners.run_in_docker nvidia-smi --name testing --gpus 0,1
       # Simple command to ls the workspace in the Docker.
       python -m runners.run_in_docker ls

    or use the Makefile:

    .. code-block:: bash

       # Runs a Docker container with two GPUs.
       make run_in_container command="nvidia-smi" name=testing gpus=0,1
       # Simple command to ls the workspace in the Docker.
       make run_in_container command="ls"

    """
    parser = ArgumentParser()
    parser.add_argument('command', type=str, nargs='+', help='command to run in docker')
    parser.add_argument('--name', type=str, default=None)
    parser.add_argument('--gpus', type=str, default='')
    args = vars(parser.parse_args())
    if len(args['command']) == 1:
        args['command'] = args['command'][0].split(' ')

    runner = DockerRunner()
    gpus = os.getenv('CUDA_VISIBLE_DEVICES', "")
    name = os.getenv('NAME', "")
    name = runner.run(args['command'], gpus, name)
    subprocess.call(['docker', 'logs', '-f', name])

if __name__ == '__main__':
    run_in_docker()