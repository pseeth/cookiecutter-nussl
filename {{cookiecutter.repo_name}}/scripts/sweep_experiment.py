import sys
sys.path.insert(0, '.')

from runners.experiment_utils import load_experiment, save_experiment
from runners.utils import load_yaml, dump_yaml, parse_yaml
from . import cmd, document_parser
from src import logging
import os
import itertools
import copy
from argparse import ArgumentParser

def replace_item(obj, key, replace_value):
    """
    Recursively replaces any matching key in a dictionary with a specified replacement
    value.
    
    Args:
        obj (dict): Dictionary where item is being replaced.
        key (obj): Key to replace in dictionary.
        replace_value (obj): What to replace the key with.
    
    Returns:
        dict: Dictionary with everything of that key replaced with the specified value.
    """
    for k, v in obj.items():
        if isinstance(v, dict):
            obj[k] = replace_item(v, key, replace_value)
    if key in obj:
        obj[key] = replace_value
    return obj

def nested_set(element, value, *keys):
    """
    Use a list of keys to replace a value in a dictionary. The result will look 
    like::

        element[key1][key2][key3]...[keyn] = value
    
    Args:
        element (dict): Dictionary to iteratively query.
        value ([type]): Value to set at the end of the query
    
    Raises:
        AttributeError: first argument must be a dictionary
        AttributeError: must have at least three arguments.
    """
    if type(element) is not dict:
        raise AttributeError('nested_set() expects dict as first argument.')
    if len(keys) < 2:
        raise AttributeError('nested_set() expects at least three arguments, not enough given.')

    _keys = keys[:-1]
    _element = element
    for key in _keys:
        _element = _element[key]
    _element[keys[-1]] = value

def update_config_with_sweep(config, sweep, combo):
    """
    Update a configuration with a sweep. The experiment configuration is updated using
    the sweep and combo. The sweep contains every key that needs to be updated 
    in the configuration. If something in the sweep is a list, then the associated
    key is updated with only one of the elements of the list. Which element is
    specified by 'combo. Otherwise, the value from sweep is used.
    
    Args:
        config (dict): The experiment configuration that is being updated.
        sweep (dict): The full sweep that is used to update the configuration.
        combo (dict): The specific values for keys in the sweep that are lists.
    
    Returns:
        dict: An updated configuration using the sweep and combo arguments.
    """
    multiple_parameters = {}
    keys_to_pop = []
    for key in combo:
        if 'multiple_parameters' in key:
            multiple_parameters.update(combo[key])
            keys_to_pop.append(key)

    combo.update(multiple_parameters)
    this_sweep = copy.deepcopy(sweep)
    this_sweep.update(combo)
    for k in keys_to_pop:
        this_sweep.pop(k)
    
    logging_str = ''
    for key in this_sweep:
        logging_str += f", {key}: {this_sweep[key]}"
    logging.info(logging_str)

    this_experiment = copy.deepcopy(config)
    notes = this_experiment['info'].pop('notes', '')
    notes += logging_str
    this_experiment['info']['notes'] = notes

    for key in this_sweep:
        if '.' in key: # replace | with .
            # specific update
            loc = key.split('.')
            nested_set(this_experiment, this_sweep[key], *loc)
        else:
            # global update
            this_experiment = replace_item(
                this_experiment, 
                key,
                this_sweep[key]
            )
    return this_experiment

def create_experiments(path_to_yml_file):
    """
    The main logic of this script. Takes the path to the base experiment file and
    loads the configuration. It then goes through the sweep dictionary kept in that
    base experiment file. The sweep dictionary tells how to update the configuration.
    The Cartesian product of all the possible settings specified by sweep is taken.
    Each experiment is updated accordingly. The length of the Cartesian product of
    the sweep is the number of experiments that get created. 
    
    Args:
        path_to_yml_file (str): Path to base experiment file.
    
    Returns:
        tuple: 2-element tuple containing

            - experiments (*list*):  List of paths to .yml files that define the generated
                experiments.
            - cache_experiments (*list*):  List of paths to .yml files that define the 
                experiments used for creating caches if any.
    """
    base_experiment = load_yaml(path_to_yml_file)
    sweep = base_experiment.pop('sweep', [])
    experiments = []
    cache_experiments = []

    for k, _sweep in enumerate(sweep):
        lists = []
        keys = []
        for key in _sweep:
            if isinstance(_sweep[key], list):
                keys.append(key)
                lists.append(_sweep[key])

        _combos = list(itertools.product(*lists))
        combos = []
        for c in _combos:
            combos.append({keys[i]: c[i] for i in range(len(c))})

        if _sweep['populate_cache']:
            # Create a single experiment for creating dataset caches.
            cache_config, cache_exp, cache_path_to_yml_file = load_experiment(path_to_yml_file)
            cache_config.pop('sweep')
            this_experiment = update_config_with_sweep(
                cache_config, _sweep, combos[0]
            )
            this_experiment['train_config']['num_epochs'] = 0
            this_experiment['dataset_config']['overwrite_cache'] = True

            if 'num_cache_workers' in _sweep:
                this_experiment['train_config']['num_workers'] = (
                    _sweep['num_cache_workers']
                )
            cache_experiments.append(save_experiment(this_experiment, cache_exp))

        for j, c in enumerate(combos):
            # Sweep across all the possible combinations and update.
            config, exp, _path_to_yml_file = load_experiment(path_to_yml_file)
            config.pop('sweep')

            this_experiment = update_config_with_sweep(config, _sweep, c)
            experiments.append(save_experiment(this_experiment, exp))
        
    return experiments, cache_experiments
        
def create_pipeline(path_to_yml_files, script_name, num_jobs=1, num_gpus=0,
    run_in='host', blocking=False, prefix='-p', extra_cmd_args=''):
    """
    Takes a list of yml files, a script name, and some configuration options and
    creates a pipeline that can be passed to :py:mod:`scripts.pipeline` so that each
    job is executed accordingly.

    Args:
        path_to_yml_files (list): List of paths to each .yml file that contains the 
            generated experiment configuration from the sweep.
        script_name (str): What script to use, should exist in :py:mod:`scripts`.
        num_jobs (int, optional): Number of jobs to be used to run each of these jobs. 
            Is used as the max_workers argument in 
            :py:class:`runners.script_runner_pool.ScriptRunnerPool`. Defaults to 1.
        num_gpus (int, optional): Number of GPUs to use for each job. Defaults to 0.
        run_in (str, optional): Whether to run on 'host' or 'container'. 
            Defaults to 'host'.
        blocking (bool, optional): Whether to block on each job (forces the jobs to run
            sequentially). Defaults to False.
        prefix (str, optional): The prefix to use before the command (either '-p' or '-y').
            Defaults to '-p'.
        extra_cmd_args (str, optional): Any extra command line arguments that pipeline may
            need to run the script, specified as a str as if it was on the command line. 
            Defaults to ''.
    
    Returns:
        dict: A dictionary containing the sequence of pipelines that is later dumped to
            YAML so it can be passed to :py:mod:`scripts.pipeline`.
    """
    pipeline = {
        'jobs': [],
        'num_jobs': num_jobs
    }
    for p in path_to_yml_files:
        _job = {
            'script': script_name,
            'config': f"""{prefix} "{p}" {extra_cmd_args}""",
            'run_in': run_in,
            'blocking': blocking,
            'num_gpus': num_gpus,
        }
        pipeline['jobs'].append(_job)
    return pipeline

def sweep_experiment(path_to_yml_file, num_jobs=1, num_gpus=0, run_in='host'):
    """
    Takes a base experiment file and sweeps across the 'sweep' key in it, replacing
    values as needed. Results in the Cartesian product of all of the parameters that are
    being swept across. Also creates pipeline files that can be passed to 
    :py:mod:`scripts.pipeline` so that everything can be run in sequence easily, or
    in parallel as determined by num_jobs.

    The sweep config is used to replace dictionary keys and create experiments
    on the fly. A separate experiment will be created for each sweep discovered. The
    set of experiments can then be submitted to the job runner in parallel or in sequence.
    If one of the arguments is a list, then it will loop across each of the items in the
    list creating a separate experiment for each one. There's no real error checking so be careful
    when setting things up as creating invalid or buggy experiments (e.g. num_frequencies
    and n_fft don't match) is possible.

    If there is a '.' in the key, then it is an absolute path to the exact value to update
    in the configuration. If there isn't, then it is a global update for all matching keys.

    Here's a simple example of a sweep configuration that specifies the STFT parameters
    and sweeps across the number of hidden units and embedding size:

    .. code-block:: yaml

       sweep:
          - n_fft: 128
            hop_length: 64
            num_frequencies: 65 # n_fft / 2 + 1
            num_features: 65
            model_config.modules.recurrent_stack.args.hidden_size: [50, 100] # specific sweep, delimited by '.'
            embedding_size: [10, 20] # global sweep
            cache: '${CACHE_DIRECTORY}/musdb_128'
            populate_cache: true # controls whether to create a separate experiment for caching
            num_cache_workers: 60 # how many workers to use when populating the cache

    The above creates 5 experiments, across the Cartesian product of hidden size and
    embedding size, +1 for the caching experiment::

        - caching "experiment" where training data is prepared
        - hidden_size = 50, embedding_size = 10  # 1st experiment
        - hidden_size = 50, embedding_size = 20  # 2nd experiment
        - hidden_size = 100, embedding_size = 10 # 3rd experiment
        - hidden_size = 100, embedding_size = 20 # 4th experiment

    Each sweep within an item of the list should use the same cache. The cache is 
    created as a separate experiment. For example, if we want to sweep across STFT parameters,
    then we need different caches as different STFTs will result in different training data.

    .. code-block:: yaml

       sweep:
          - n_fft: 128
            hop_length: 64
            num_frequencies: 65 # n_fft / 2 + 1
            num_features: 65
            model_config.modules.recurrent_stack.args.hidden_size: [50, 100] # specific sweep, delimited by '.'
            embedding_size: [10, 20] # global sweep
            cache: '${CACHE_DIRECTORY}/musdb_128'
            populate_cache: true # controls whether to create a separate experiment for caching
            num_cache_workers: 60 # how many workers to use when populating the cache
        
          - n_fft: 256
            hop_length: 64
            num_frequencies: 129 # n_fft / 2 + 1
            num_features: 129
            model_config.modules.recurrent_stack.args.hidden_size: [50, 100] # specific sweep, delimited by '.'
            embedding_size: [10, 20] # global sweep
            cache: '${CACHE_DIRECTORY}/musdb_256'
            populate_cache: true # controls whether to create a separate experiment for caching
            num_cache_workers: 60 # how many workers to use when populating the cache

    Now we create 10 experiments, 4 for each item in the list, +1 for each cache.

    Args:
        path_to_yml_file ([type]): Path to the configuration for the base experiment. 
            This will be expanded by the script, filling in the values defined in 'sweep' 
            accordingly, and create new experiments.
        num_jobs (int): Controls the number of jobs to use in the created pipelines. 
            Defaults to 1.
        num_gpus (int): Controls the number of gpus to use in the created pipelines.
            Defaults to 0.
        run_in (str): Run jobs in containers or on the host ('container' or 'host').
            Defaults to host.
    """
    experiments, cache_experiments = create_experiments(path_to_yml_file)

    scripts = ['train', 'evaluate', 'analyze']
    pipeline_ymls = []

    base_dir = os.path.splitext(os.path.abspath(path_to_yml_file))[0]
    base_dir = base_dir.split('/')
    base_dir.insert(-1, 'out')
    base_dir = os.path.join('/', *base_dir)
    os.makedirs(base_dir, exist_ok=True)

    # Block on cache creation
    if cache_experiments:
        cache_pipeline = create_pipeline(
            cache_experiments, 'train', num_jobs=num_jobs
        )
        output_path = os.path.join(base_dir, 'cache.yml')
        dump_yaml(cache_pipeline, output_path)
        pipeline_ymls.append(output_path)
    
    for s in scripts:
        num_gpus = 0 if s == 'analyze' else num_gpus
        num_jobs = 1 if s == 'analyze' else num_jobs
        extra_cmd_args = ''
        if s == 'analyze':
            extra_cmd_args += '--use_gsheet true'
        run_in = 'host' if s == 'analyze' else run_in
        pipeline = create_pipeline(
            experiments, 
            s, 
            num_jobs=num_jobs,
            num_gpus=num_gpus,
            run_in=run_in,
            extra_cmd_args=extra_cmd_args
        )
        output_path = os.path.join(base_dir, f'{s}.yml')
        dump_yaml(pipeline, output_path)
        pipeline_ymls.append(output_path)
    
    pipeline = create_pipeline(
        pipeline_ymls, 
        'pipeline', 
        num_jobs=1, 
        blocking=True,
        run_in='host',
        prefix='-y'
    )

    output_path = os.path.join(base_dir, 'pipeline.yml')
    dump_yaml(pipeline, output_path)

    logging.info(
        f'Inspect the created pipeline files' 
        f' before running them! @ {output_path}'
    )

@document_parser('sweep_experiment', 'scripts.sweep_experiment.sweep_experiment')
def build_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "-p",
        "--path_to_yml_file",
        type=str,
        required=True,
        help="""Path to the configuration for the base experiment. This will be expanded
        by the script, filling in the values defined in 'sweep' accordingly, and create new
        experiments.
        """
    )
    parser.add_argument(
        '--num_jobs', 
        help="Controls the number of jobs to use in the created pipelines. Defaults to 1.",
        required=False,
        type=int, 
        default=1
    )
    parser.add_argument(
        '--num_gpus', 
        help="Controls the number of gpus to use in the created pipelines. Defaults to 0.",
        required=False, 
        type=int,
        default=0
    )
    parser.add_argument(
        '--run_in', 
        help="Run jobs in containers or on the host ('container' or 'host'). Defaults to host.",
        required=False, 
        type=str,
        default='host'
    )
    return parser

if __name__ == "__main__":
    cmd(sweep_experiment, build_parser)