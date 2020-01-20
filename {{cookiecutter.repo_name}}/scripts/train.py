from runners.experiment_utils import load_experiment, save_experiment
from src import dataset, train, model
from src.utils import loaders
import logging
from runners.utils import load_yaml
from . import cmd, document_parser
from argparse import ArgumentParser
import os

def train_experiment(path_to_yml_file):
    """
    Starts a training job for the experiment defined at the path specified. Fits the
    model accordingly.
    
    Args:
        path_to_yml_file (str): Path to the configuration for the experiment that 
        is getting trained. The script will take the configuration and launch a 
        training job for the experiment.
    """
    config, exp, path_to_yml_file = load_experiment(path_to_yml_file)
    
    train_class = config['train_config'].pop('class')
    TrainerClass = getattr(train, train_class)

    if 'train' not in config['datasets']:
        logging.error('Train dataset must be specified!')

    _datasets = {}

    for key in ['train', 'val']:
        if key in config['datasets']:
            _datasets[key] = loaders.load_dataset(
                config['datasets'][key]['class'],
                config['datasets'][key]['folder'],
                config['dataset_config']
            )
        else:
            _datasets[key] = None

    _model = loaders.load_model(config['model_config'])
    _trainer = TrainerClass(
        config['info']['output_folder'],
        _datasets['train'],
        _model,
        config['train_config'],
        validation_data=_datasets['val'],
        use_tensorboard=config['train_config'].pop('use_tensorboard', False),
        experiment=exp
    )
    _trainer.fit()

@document_parser('train_experiment', 'scripts.train.train')
def build_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "-p",
        "--path_to_yml_file",
        type=str,
        required=True,
        help="""Path to the configuration for the experiment that is getting trained. The
        script will take the configuration and launch a training job for the experiment.
        """
    )
    return parser

if __name__ == '__main__':
    cmd(train_experiment, build_parser)