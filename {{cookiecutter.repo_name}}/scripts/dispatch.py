from . import cmd, document_parser
from argparse import ArgumentParser
import subprocess
import logging
from rq import Queue, Connection
from redis import Redis
from src.utils.workers import allocate_resources_and_queue

def dispatch(command, name=None, depends_on=None, num_gpus=0, blocking=False, 
             redis_path='redis.sock'):
    """
    [summary]
    
    [extended_summary]
    
    Args:
        command ([type]): [description]
        name ([type], optional): [description]. Defaults to None.
        depends_on ([type], optional): [description]. Defaults to None.
        num_gpus (int, optional): [description]. Defaults to 0.
        blocking (bool, optional): [description]. Defaults to False.
        redis_path (str, optional): [description]. Defaults to 'redis.sock'.
    """
    with Connection(Redis(unix_socket_path=redis_path)):
        _queue = Queue('dispatch')
        _queue.enqueue(
            allocate_resources_and_queue, 
            args=(command,),
            kwargs={'num_gpus': num_gpus, 'depends_on': depends_on, 
                    'blocking': blocking, 'name': name, 'redis_path': redis_path}
        )

@document_parser('dispatch', 'scripts.dispatch.dispatch')
def build_parser():
    parser = ArgumentParser()
    parser.add_argument(
        'command',
        type=str,
        help='Command to run.'
    )
    parser.add_argument(
        '--name',
        required=False,
        type=str,
        help='Unique name of this job. Used to look up this job if other jobs are dependent on this one.'
    )
    parser.add_argument(
        '--num_gpus',
        required=False,
        type=int,
        default=0,
        help='Number of GPUs needed by this job.'
    )
    parser.add_argument(
        '--depends_on',
        required=False,
        type=str,
        help="""
            Unique name of the job that this job depends on. This job will not run
            until that job is complete.
            """
    )
    parser.add_argument(
        '--blocking', 
        help="Finish this job before proceeding to next.", 
        action='store_true'
    )
    return parser

if __name__ == "__main__":
    cmd(dispatch, build_parser)