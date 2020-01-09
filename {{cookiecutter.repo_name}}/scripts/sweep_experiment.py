import sys
sys.path.insert(0, '.')

from runners.experiment_utils import load_experiment, save_experiment
from runners.utils import load_yaml, dump_yaml, build_parser_for_yml_script, parse_yaml
from cookiecutter_repo import logging
import os
import itertools
import copy

def replace_item(obj, key, replace_value):
    for k, v in obj.items():
        if isinstance(v, dict):
            obj[k] = replace_item(v, key, replace_value)
    if key in obj:
        obj[key] = replace_value
    return obj

def nested_set(element, value, *keys):
    if type(element) is not dict:
        raise AttributeError('nested_set() expects dict as first argument.')
    if len(keys) < 2:
        raise AttributeError('nested_set() expects at least three arguments, not enough given.')

    _keys = keys[:-1]
    _element = element
    for key in _keys:
        _element = _element[key]
    _element[keys[-1]] = value

def update_config_with_sweep(config, sweep, combo, logging_str):
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

    for key in this_sweep:
        logging_str += f"\n\t\t{key}: {this_sweep[key]}"
    logging.info(logging_str)

    this_experiment = copy.deepcopy(config)
    
    for key in this_sweep:
        if '.' in key:
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

def sweep_experiment(path_to_yml_file):
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
            cache_config, cache_exp, cache_path_to_yml_file = load_experiment(path_to_yml_file)
            cache_config.pop('sweep')
            logging_str = (
                f"\n\tCreating cache population experiment {0}/{len(combos)} "
                f"for sweep {0}/{len(sweep)}"
            )
            this_experiment = update_config_with_sweep(
                cache_config, _sweep, combos[0], logging_str
            )
            this_experiment['train_config']['num_epochs'] = 0
            this_experiment['dataset_config']['overwrite_cache'] = True

            if 'num_cache_workers' in _sweep:
                this_experiment['train_config']['num_workers'] = (
                    _sweep['num_cache_workers']
                )
            cache_experiments.append(save_experiment(this_experiment, cache_exp))

        for j, c in enumerate(combos):
            config, exp, _path_to_yml_file = load_experiment(path_to_yml_file)
            config.pop('sweep')

            logging_str = (
                f"\n\tCreating experiment {j+1}/{len(combos)} "
                f"for sweep {k+1}/{len(sweep)}"
            )
            this_experiment = update_config_with_sweep(config, _sweep, c, logging_str)
            experiments.append(save_experiment(this_experiment, exp))
        
    return experiments, cache_experiments
        
def create_pipeline(
    path_to_yml_files, 
    script_name,
    num_jobs=1,
    num_gpus=0,
    run_in='container',
    blocking=False,
):
    pipeline = {
        'jobs': [],
        'num_jobs': num_jobs
    }
    for p in path_to_yml_files:
        _job = {
            'script': script_name,
            'config': p,
            'run_in': run_in,
            'blocking': blocking,
            'num_gpus': num_gpus,
        }
        pipeline['jobs'].append(_job)
    return pipeline

if __name__ == "__main__":
    parser = build_parser_for_yml_script()
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
        help="Run jobs in containers or on the host ('container' or 'host'). Defaults to container.",
        required=False, 
        type=str,
        default='container'
    )
    args = vars(parser.parse_args())
    experiments, cache_experiments = sweep_experiment(args['spec'])

    scripts = {
        'train': 'scripts/train.py', 
        'evaluate': 'scripts/evaluate.py', 
        'analyze': 'scripts/analyze.py'
    }

    pipeline_ymls = []

    base_dir = os.path.splitext(os.path.abspath(args['spec']))[0]
    base_dir = base_dir.split('/')
    base_dir.insert(-1, 'out')
    base_dir = os.path.join('/', *base_dir)
    os.makedirs(base_dir, exist_ok=True)

    # Block on cache creation
    if cache_experiments:
        cache_pipeline = create_pipeline(
            cache_experiments, scripts['train'], num_jobs=args['num_jobs']
        )
        output_path = os.path.join(base_dir, 'cache.yml')
        dump_yaml(cache_pipeline, output_path)
        pipeline_ymls.append(output_path)
    
    for s in scripts:
        num_gpus = 0 if s == 'analyze' else args['num_gpus']
        num_jobs = 1 if s == 'analyze' else args['num_jobs']
        pipeline = create_pipeline(
            experiments, 
            scripts[s], 
            num_jobs=num_jobs,
            num_gpus=num_gpus
        )
        output_path = os.path.join(base_dir, f'{s}.yml')
        dump_yaml(pipeline, output_path)
        pipeline_ymls.append(output_path)
    
    pipeline = create_pipeline(
        pipeline_ymls, 
        'scripts/pipeline.py', 
        num_jobs=1, 
        blocking=True,
        run_in='host'
    )

    output_path = os.path.join(base_dir, 'pipeline.yml')
    dump_yaml(pipeline, output_path)

    logging.info(
        f'Inspect the created pipeline files' 
        f' before running them! @ {output_path}'
    )