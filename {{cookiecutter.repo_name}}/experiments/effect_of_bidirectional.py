import sys
sys.path.insert(0, '.')

"""
This is a simple experiment file. Use these to create experiments with different
configurations of an algorithm or a model (e.g. by doing a parameter sweep). This
one creates two experiments for music separation. The only difference between
the experiments is that one has bidirectionality in the model and the other does not.

The script outputs a .yml file that contains all the experiments created in a format
that can be fed to scripts/pipeline.py. That script will run all the jobs in 
parallel.

What you need: some base experiment file that you will be modifiying. Here, these are:
    base/
        music_dpcl.yml
        speech_dpcl.yml

Be sure that you have sourced your environment variables before running this script.
Other than that, the structure of this script is up to you.
"""

from runners.experiment_utils import load_experiment, save_experiment
from runners.utils import load_yaml, dump_yaml
from cookiecutter_repo import logging
import os

def load_and_modify_base_experiment():
    path_to_yml_files = []

    # Create the exp that will populate the cache.
    config, exp, path_to_yml_file = load_experiment(
        'experiments/base/music_dpcl.yml'
    )
    config['train_config']['num_workers'] = 60
    config['train_config']['num_epochs'] = 0
    config['dataset_config']['overwrite_cache'] = True
    path_to_yml_file = save_experiment(config, exp)
    path_to_yml_files.append(path_to_yml_file)

    # Now create the exps that sweep over bidirectional.
    bidirectional = [True, False]
    for i, b in enumerate(bidirectional):
        config, exp, path_to_yml_file = load_experiment(
            'experiments/base/music_dpcl.yml'
        )
        # modify the experiment in some way
        config['model_config']['modules']['recurrent_stack']['bidirectional'] = b
        path_to_yml_file = save_experiment(config, exp)
        path_to_yml_files.append(path_to_yml_file)
    return path_to_yml_files

def create_pipeline(
    path_to_yml_files, 
    script_name,
    num_jobs=1,
):
    pipeline = {
        'jobs': [],
        'num_jobs': num_jobs
    }
    for p in path_to_yml_files:
        _job = {
            'script': script_name,
            'config': p,
            'run_in': 'container',
            'blocking': False,
            'num_gpus': 0,
        }
        pipeline['jobs'].append(_job)
    return pipeline

if __name__ == "__main__":
    path_to_yml_files = load_and_modify_base_experiment()
    scripts = {
        'train': 'scripts/train.py', 
        'evaluate': 'scripts/evaluate.py', 
        'analyze': 'scripts/analyze.py'
    }

    pipeline_ymls = []

    base_dir = os.path.splitext(os.path.abspath(__file__))[0]
    os.makedirs(base_dir, exist_ok=True)

    for s in scripts:
        offset = 0 if s == 'train' else 1
        pipeline = create_pipeline(
            path_to_yml_files[offset:], 
            scripts[s],
            num_jobs=2
        )
        if 'train':
            pipeline['jobs'][0]['blocking'] = True
            for i in range(1, len(pipeline['jobs'])):
                pipeline['jobs'][i]['num_gpus'] = 1

        output_path = os.path.join(base_dir, f'{s}.yml')
        dump_yaml(pipeline, output_path)
        pipeline_ymls.append(output_path)
    
    pipeline = create_pipeline(pipeline_ymls, 'scripts/pipeline.py', num_jobs=1)
    output_path = os.path.join(base_dir, 'pipeline.yml')
    dump_yaml(pipeline, output_path)

    logging.info(
        f'Inspect the created pipeline files' 
        f'before running them!'
    )