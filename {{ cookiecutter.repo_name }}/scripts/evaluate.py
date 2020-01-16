import sys
sys.path.insert(0, '.')

from runners.experiment_utils import load_experiment, save_experiment
from src import dataset, test, model
from src.utils import loaders
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

    _tester = test.EvaluationRunner(
        testers,
        config['algorithm_config'],
        _datasets['test'],
        config['info']['output_folder'],
        max_workers=config['test_config']['num_workers'],
        use_blocking_executor=config['test_config']['use_blocking_executor']
    )
    _tester.run()

if __name__ == '__main__':
    parser = build_parser_for_yml_script()
    args = vars(parser.parse_args())
    main(args['spec'])