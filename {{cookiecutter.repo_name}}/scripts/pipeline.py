"""
Takes a .yml file with structure as follows:

    script: path/to/script/name.py
    config: path/to/yml/config.yml
    run_in: 'host' or 'container'
    num_gpus: how many gpus (default: 0)
    num_cpus: how many cpus (default: 1)
    blocking: whether to block on this job or not (default: false)

Could also be multiple jobs:
    parallelize: whether to parallelize each job (default: false)
    num_jobs: how many jobs to run in parallel (default: 1)

    jobs:
    - script: script1.py
      config: config1.yml
    - script: script2.py
      config: config2.yml
    ...

The jobs get executed one after the other.
"""
import sys
sys.path.insert(0, '.')

from runners.utils import build_parser_for_yml_script, parse_yaml
from runners.script_runner_pool import ScriptRunnerPool
from cookiecutter_repo import logging
from multiprocessing import cpu_count

def main(path_to_yml_file):
    spec = parse_yaml(path_to_yml_file)

    num_jobs = min(cpu_count(), spec.pop('num_jobs', 1))

    logging.info(
        f"\n  Executing scripts with num_jobs: {num_jobs}"
    )

    pool = ScriptRunnerPool(max_workers=num_jobs)
    pool.submit(spec['jobs'])

if __name__ == "__main__":
    parser = build_parser_for_yml_script()
    args = vars(parser.parse_args())
    main(args['spec'])