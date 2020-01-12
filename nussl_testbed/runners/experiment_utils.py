try:
    from comet_ml import Experiment, ExistingExperiment
    comet_ml_imported = True
except:
    comet_ml_imported = False

from .utils import (
    load_yaml, 
    dump_yaml,
    make_random_string, 
    env_variables, 
    build_parser_for_yml_script,
    flatten
)
import os
import logging

def save_experiment(config, exp=None):
    """Saves a configuration of an experiment to an experiment directory.
    """
    logging.info(f"Creating experiment folder @ {config['info']['output_folder']}")
    os.makedirs(config['info']['output_folder'], exist_ok=True)

    output_path_to_yml = os.path.join(config['info']['output_folder'], 'config.yml')
    dump_yaml(config, output_path_to_yml)
    logging.info(f"Saved config to @ {output_path_to_yml}")

    if exp:
        exp.log_parameters(flatten(config))
        with open(output_path_to_yml, 'r') as f:
            exp.set_code(f.read(), overwrite=True)
    return output_path_to_yml

def load_experiment(path_to_yml_file):
    config = load_yaml(path_to_yml_file)
    api_key = os.getenv('COMET_API_KEY', None)
    exp = None        
    
    if config['info']['experiment_key'] == '${EXPERIMENT_KEY}':
        if api_key and comet_ml_imported:
            exp = Experiment(
                api_key=api_key, 
                project_name=config['info']['project_name']
            )
            exp_key = exp.get_key()
        else:
            exp_key = make_random_string(20)
        
        os.environ['EXPERIMENT_KEY'] = exp_key

        _env_variables = env_variables + ['EXPERIMENT_KEY']
        config = load_yaml(path_to_yml_file, _env_variables)
        config['info']['experiment_key'] = exp_key
        path_to_yml_file = save_experiment(config, exp)
    else:
        logging.info(
            f"Experiment is already set up @ {config['info']['output_folder']}!"
        )
        if comet_ml_imported:
            exp = ExistingExperiment(
                api_key=api_key,
                previous_experiment=config['info']['experiment_key']
            )
    
    return config, exp, path_to_yml_file