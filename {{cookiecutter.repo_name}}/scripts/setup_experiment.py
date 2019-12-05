import sys
sys.path.insert(0, '.')

from runners.experiment_utils import load_experiment, save_experiment
from runners.utils import build_parser_for_yml_script
from cookiecutter_repo import logging
import os

def main(path_to_yml_file):
    config, exp, path_to_yml_file = load_experiment(path_to_yml_file)      
    config['info']['test'] = 'TESTING'
    save_experiment(config, exp)

if __name__ == '__main__':
    parser = build_parser_for_yml_script()
    args = vars(parser.parse_args())
    main(args['spec'])