import sys
sys.path.insert(0, '.')

from runners.experiment_utils import load_experiment, save_experiment
from src import dataset, train, model
from src.utils import loaders
import logging
from runners.utils import build_parser_for_yml_script, load_yaml
from argparse import ArgumentParser
import os

def main(path_to_yml_file):
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

if __name__ == '__main__':
    parser = build_parser_for_yml_script()
    args = vars(parser.parse_args())
    main(args['spec'])