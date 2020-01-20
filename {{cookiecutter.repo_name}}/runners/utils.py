import collections
from concurrent.futures import ProcessPoolExecutor, as_completed
import yaml
import os
from multiprocessing import cpu_count
import logging
from .config import default_script_args
import random
import string

#: List of environment variables to look for and replace. 
env_variables = [
    'DATA_DIRECTORY',
    'CACHE_DIRECTORY',
    'ARTIFACTS_DIRECTORY',
    'NUSSL_DIRECTORY',
]

def modify_yml_with_env(yml, env_variables):
    """
    Replaces specific substrings in a string or elsewhere with
    their corresponding environment variables. The environment variables it currently
    replaces are: DATA_DIRECTORY, CACHE_DIRECTORY, ARTIFACTS_DIRECTORY, and 
    NUSSL_DIRECTORY. Descriptions of these are in setup/environment/default.sh.

    Args:
        yml (str): A string containing the YML code (unparsed). Things in curly braces
             in the string are modified by passing in the data in :py:obj:`runners.utils.env_variables`.
        env_variables (list): A list of strings containing what environment variables
            to replace.
    
    Returns:
        str: YML string with the environment variables replaced.
    """
    for _env in env_variables:
        _env_str = f'${{{_env}}}'
        if _env_str in yml:
            yml = yml.replace(_env_str, os.getenv(_env, ""))
    return yml

def load_yaml(path_to_yml, env_variables=env_variables):
    """
    Loads a YAML file and modifies it according to the environment variables using
    :py:func:`runners.utils.modify_yml_with_env`.
    
    Args:
        path_to_yml (str): Path to the YML file.
        env_variables (list): A list of strings containing what environment variables
            to replace.
    
    
    Returns:
        dict: Parsed and loaded YAML into a dictionary.
    """
    with open(path_to_yml, 'r') as f:
        yml = modify_yml_with_env(f.read(), env_variables)
        data = yaml.load(yml, Loader=yaml.FullLoader)
    return data

def dump_yaml(data, path_to_yml):
    """
    Dump data to a yml file at a specified location.
    
    Args:
        data (obj): Whatever data to dump to the yml file, as long as it can be
            serialized to YAML. Typically a dictionary.
        path_to_yml (str): Where to save the data.
    """
    with open(path_to_yml, 'w') as f:
        yaml.dump(data, f)

def parse_yaml(path_to_yml, jobs=True):
    """
    Parses a YAML file, replacing necessary environment variables and putting 
    it in an expected form for the scripts.
    
    Args:
        path_to_yml (str): Path to yml file to be parsed.
        jobs (bool, optional): Whether to convert it so that it's a sequence
            of jobs if `jobs` is not defined in spec. Defaults to True.
    
    Returns:
        dict: Loaded dictionay, modified by environment variables and depending on
            jobs.
    """
    _spec = load_yaml(path_to_yml)
    spec = {}

    if 'jobs' not in _spec and jobs:
        spec['jobs'] = [_spec]
    else:
        spec = _spec
    return spec

def prepare_script_args(spec):
    """
    Uses the default script args if those items are not specified for
    the script.
    
    Args:
        spec (dict): Script args to modify with defaults as needed.
    
    Returns:
        dict: Modified dictionary with values as needed.
    """
    spec['run_in'] = spec.pop('run_in', default_script_args['run_in'])
    spec['num_gpus'] = spec.pop('num_gpus', default_script_args['num_gpus'])
    spec['blocking'] = spec.pop('blocking', default_script_args['blocking'])
    return spec

def disp_script(spec):
    """
    Displays the arguments for a script in a readable fashion in
    logging.
    
    Args:
        spec (dict): Dictionary containing script parameters.
    """
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
    
    Args:
        source (dict): Source dictionary that gets updated
        overrides (dict): Dictionary with items to update in source
            dict.
    
    Returns:
        (dict): Updated source dictionary.
    """
    for key, value in overrides.items():
        if isinstance(value, collections.Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source

def flatten(d, parent_key='', sep='_'):
    """
    Flattens a dictionary so that it only has one level. A sequence of keys
    will result in a key that is like::

        { key1_key2_key3: value }

    from::
        
        { key1: {key2: {key3: val} } }

    This is done recursively.
    
    Args:
        d ([type]): Dictionary that is being flattened.
        parent_key (str, optional): The key above this one (used in recursion). 
            Defaults to ''.
        sep (str, optional): Delimiter between keys. Defaults to '_'.
    
    Returns:
        dict: flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def make_random_string(length=10):
    """
    Makes a random alphanumeric string of some length
    
    Args:
        length (int, optional): Length of the random string to return. Defaults to 10.
    
    Returns:
        str: Random alphanumeric string of the specified length.
    """
    return ''.join(
        random.choice(string.ascii_lowercase + string.digits) 
        for _ in range(length)
    )