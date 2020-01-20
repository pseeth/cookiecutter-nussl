import docker
import GPUtil
from .config import volumes
import os
import logging

class DockerRunner(object):
    """
    This class just creates a Docker container from the given image and runs it.
    If the image is not specified, it looks in the environment variable called
    'DOCKER_IMAGE_NAME'. If that doesn't exist, it throws a warning.

    If there are gpus available, it uses the NVIDIA docker runtime to access them
    through GPU passthrough. If no GPUs are available, it uses the standard runtime.

    The class mounts volumes in the host into the container at specified paths. These
    paths are specified in config.py and are accessible via environment variables. 

    Args:
        image (str): Image to use when running inside Docker. If not specified, it 
            uses whatever is in the environment variable DOCKER_IMAGE_NAME. If that
            isn't specified, it throws a warning.
    """
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

    def run(self, command, gpus, name=None, detach=True):
        """
        Run a given command in a Docker container. This detaches from the container
        completely by default. 

        Args:
            command (str): Command to run inside the container.
            gpus (str): What GPUs to use. For example gpus='0,1,2' will result in the
                container having access to the first 3 GPUs on the system.
            name (str): The container should be named something. If name is not provided
                (default) then a name is chosen by parsing the command. Docker container
                names must be unique.
            detach (bool): Whether to detach from the container after launching (running
                it in the background) or to stay attached to the container.
        """
        logging.info(f'Running: {command} on GPUs: {gpus}')

        ports = None
        user = os.getenv('USER')
        if not name:
            name = command[0] + command[-1].replace('experiments', 'exp')
            name = name.replace('_', '-')
            name = name.replace(' ', '-')
            name = name.replace('/', '.')
            logging.info(f'Docker container name: {name}')
        if command[0] == 'jupyter':
            #forward a port
            external_port = os.getenv('JUPYTER_HOST_PORT', 8888)
            ports = {'8888': ('0.0.0.0', external_port)}
        elif command[0] == 'tensorboard':
            external_port = os.getenv('TENSORBOARD_HOST_PORT', 6006)
            ports = {'6006': ('0.0.0.0', external_port)}
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
            detach=detach,
            stderr=True,
            stdout=True,
        )
        return name