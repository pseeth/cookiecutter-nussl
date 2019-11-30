import docker
import GPUtil
from multiprocessing import cpu_count
from .config import volumes
import os
import argparse
import subprocess
import logging

class DockerRunner(object):
    def __init__(self, image=None):
        self.num_gpus = GPUtil.getAvailable(order = 'first', limit = 1000)
        if self.num_gpus:
            self.runtime = 'nvidia'
        else:
            self.runtime = 'runc'
        self.container = None
        self.volumes = volumes
        self.client = docker.from_env()
        self.image = os.getenv('DOCKER_IMAGE_NAME', image)
        if not self.image:
            logging.debug(
                'image is None! Either DOCKER_IMAGE_NAME environment variable is not set '
                'or image was not defined when instantiating DockerRunner.'
            )

    def run(self, command, gpus, name=None):
        logging.info(f'Running: {command} on GPUs: {gpus}')

        ports = None
        user = os.getenv('USER')
        if not name:
            name = command[0] + '-' + command[-1].replace('experiments', 'exp')
            name = name.replace('_', '-')
            name = name.replace(' ', '-')
            name = name.replace('/', '.')
            logging.info(f'Docker container name: {name}')
        if command[0] == 'jupyter':
            #forward a port
            external_port = os.getenv('JUPYTER_HOST_PORT')
            ports = {'8888': ('0.0.0.0', external_port)}
            command.append('--ip=0.0.0.0')
        self.container = self.client.containers.run(
            image=self.image,
            auto_remove=True,
            runtime=self.runtime,
            ipc_mode='host',
            command=command,
            working_dir="/workspace",
            volumes=self.volumes,
            entrypoint="",
            ports=ports,
            user=user,
            name=name,
            environment=[
                f"NVIDIA_VISIBLE_DEVICES={gpus}",
                f"COMET_API_KEY={os.getenv('COMET_API_KEY')}",
                f"NUSSL_DIRECTORY={os.getenv('NUSSL_DIRECTORY')}",
                f"DATA_DIRECTORY={os.getenv('DATA_DIRECTORY')}",
                f"CACHE_DIRECTORY={os.getenv('CACHE_DIRECTORY')}",
                f"ARTIFACTS_DIRECTORY={os.getenv('ARTIFACTS_DIRECTORY')}",
            ],
            detach=True,
            stderr=True,
            stdout=True,
        )
        return name