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
    flatten
)
import os
import logging

def save_experiment(config, exp=None):
    """
    Saves a configuration of an experiment to an experiment directory. If 
    exp is defined, it is an Experiment object from comet.ml whose parameters will
    be updated via config.

    Args:
        config (dict): A dictionary containing the experiment configuration. This
            should have all necessary parameters needed to recreate the experiment given
            the current codebase.
        exp (Experiment): An Experiment object that is used by comet.ml. The settings in
            the configuration dictionary are logged to the Experiment object.

    Returns:
        str: Path to the yml file that the config was saved to.
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
    """
    Loads an experiment given the path to the configuration file. If there is
    no experiment key in the info dictionary in config, then this is an 
    experiment that should be instantiated. If comet is available, then the
    experiment is instantiated by comet. If it is not available, then it is
    instantiated by producing a directory with a random name. The name of
    this directory is the experiment key used to keep track of artifacts, results, 
    and so on.
    
    Args:
        path_to_yml_file (str): Path to the yml file containing the experiment 
            configuration.
    
    Returns:
        tuple: 3-element tuple containing

            - config (*dict*):  A dictionary containing the configuration of the experiment. 
            - exp (:class:`comet_ml.Experiment`): An instantiated experiment if comet.ml is needed,  
              otherwise it is None.
            - path_to_yml_file (*str*): The path to the saved yml file (will be different 
              from the input path if the experiment in the input yml was not yet instantiated).
    """
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
        if comet_ml_imported and api_key:
            try:
                exp = ExistingExperiment(
                    api_key=api_key,
                    previous_experiment=config['info']['experiment_key']
                )
            except:
                pass
    
    return config, exp, path_to_yml_file