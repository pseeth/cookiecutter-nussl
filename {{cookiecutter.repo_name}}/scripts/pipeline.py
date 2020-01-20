from runners.utils import load_yaml
from . import cmd, document_parser
from runners.script_runner_pool import ScriptRunnerPool
from src import logging
from multiprocessing import cpu_count
from argparse import ArgumentParser

@document_parser('pipeline', 'scripts.pipeline.parallel_job_execution')
def build_parser():
    parser = ArgumentParser()
    parser.add_argument('--script', type=str, help="Path to script to run.")
    parser.add_argument('--config', type=str, help="Path to config for script.")
    parser.add_argument('--run_in', type=str, help="Run in host or container.", default='host')
    parser.add_argument('--num_gpus', type=int, help="How many GPUs to use.", default=0)
    parser.add_argument('--blocking', type=bool, help="Finish this job before proceeding to next.", default=False)
    return parser

def parallel_job_execution(script_func, jobs, parallelize=False, num_jobs=1):
    """
    Takes a .yml file with structure as follows::
    
        script: name of script in scripts/ folder
        config: path/to/yml/config.yml
        run_in: 'host' or 'container' (default: host)
        num_gpus: how many gpus (default: 0)
        blocking: whether to block on this job or not (default: false)

    Could also be multiple jobs::

        parallelize: whether to parallelize each job (default: false)
        num_jobs: how many jobs to run in parallel (default: 1)

        jobs:
        - script: script1.py
          config: config1.yml
        - script: script2.py
          config: config2.yml
        ...

    The jobs get executed in sequence or in parallel.
    
    Args:
        path_to_yml_file (str): Path to .yml file specifying the sequence
            of jobs that should be run.
    """
    num_jobs = min(cpu_count(), num_jobs)
    logging.info(
        f"\n  Executing scripts with num_jobs: {num_jobs}"
    )
    pool = ScriptRunnerPool(max_workers=num_jobs)
    pool.submit(jobs)

if __name__ == "__main__":
    cmd(lambda x: x, build_parser, parallel_job_execution)