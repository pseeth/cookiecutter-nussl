import sys
sys.path.insert(0, '.')

from runners.experiment_utils import load_experiment, save_experiment
from cookiecutter_repo import dataset, test, model
from cookiecutter_repo.utils import loaders
import logging
from runners.utils import build_parser_for_yml_script, load_yaml
from argparse import ArgumentParser
import os

def main(path_to_yml_file):
    config, exp, path_to_yml_file = load_experiment(path_to_yml_file)

    if 'test' not in config['datasets']:
        logging.error('Test dataset must be specified!')
    
    test_classes = config['test_config']['testers']
    testers = []
    for key in test_classes:
        TestClass = getattr(test, key)
        args = test_classes[key]
        testers.append((TestClass, args))

    _datasets = {}

    for key in ['test']:
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