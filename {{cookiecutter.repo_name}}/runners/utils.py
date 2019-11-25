import collections
from concurrent.futures import ProcessPoolExecutor, as_completed
import yaml
import os

def load_yaml(path_to_yml):
    with open(path_to_yml, 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return data

def modify_path_with_env(path, env):
    return os.path.join(os.getenv(env, ''), path)

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