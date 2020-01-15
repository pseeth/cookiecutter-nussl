import collections
from concurrent.futures import ProcessPoolExecutor, as_completed
import yaml
import os
from argparse import ArgumentParser
from multiprocessing import cpu_count
import logging
from .config import default_script_args
import random
import string

env_variables = [
    'DATA_DIRECTORY',
    'CACHE_DIRECTORY',
    'ARTIFACTS_DIRECTORY',
    'NUSSL_DIRECTORY',
]

def modify_yml_with_env(yml, env_variables):
    """Replaces specific substrings in a string or elsewhere with
    their corresponding environment variables. The environment variables it currently
    replaces are: DATA_DIRECTORY, CACHE_DIRECTORY, ARTIFACTS_DIRECTORY, and 
    NUSSL_DIRECTORY. Descriptions of these are in setup/environment/default.sh.
    """
    for _env in env_variables:
        _env_str = f'${{{_env}}}'
        if _env_str in yml:
            yml = yml.replace(_env_str, os.getenv(_env, ""))
    return yml

def load_yaml(path_to_yml, env_variables=env_variables):
    with open(path_to_yml, 'r') as f:
        yml = modify_yml_with_env(f.read(), env_variables)
        data = yaml.load(yml, Loader=yaml.FullLoader)
    return data

def dump_yaml(data, path_to_yml):
    with open(path_to_yml, 'w') as f:
        yaml.dump(data, f)

def build_parser_for_yml_script():
    parser = ArgumentParser()
    parser.add_argument(
        'spec', 
        type=str, 
        help= """
            Path to .yml file containing specification for reorganizing. If the only key
            is 'jobs', then we assume it points to a list of jobs with parameters
            input_path and output_path. Each job is executed one after the other. The
            structure of each .yml file is up to you.
            """
    )
    return parser

def parse_yaml(path_to_yml, jobs=True):
    _spec = load_yaml(path_to_yml)
    spec = {}

    if 'jobs' not in _spec and jobs:
        spec['jobs'] = [_spec]
    else:
        spec = _spec
    return spec

def prepare_script_args(spec):
    spec['run_in'] = spec.pop('run_in', default_script_args['run_in'])
    spec['num_gpus'] = spec.pop('num_gpus', default_script_args['num_gpus'])
    spec['blocking'] = spec.pop('blocking', default_script_args['blocking'])
    return spec

def disp_script(spec):
    logging.info(
        f"\n"
        f"  Running {spec['script']} with args:\n"
        f"    config: {spec['config']}\n"
        f"    run_in: {spec['run_in']}\n"
        f"    num_gpus: {spec['num_gpus']}\n"
        f"    blocking: {spec['blocking']}\n"
    )

def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.
    """
    for key, value in overrides.items():
        if isinstance(value, collections.Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source

def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def make_random_string(length=10):
    return ''.join(
        random.choice(string.ascii_lowercase + string.digits) 
        for _ in range(length)
    )