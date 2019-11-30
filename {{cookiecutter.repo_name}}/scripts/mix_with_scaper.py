import sys
sys.path.insert(0, '.')

from cookiecutter_repo.dataset import scaper_mix
import logging
from runners.utils import build_parser_for_yml_script, parse_yaml
from argparse import ArgumentParser
from multiprocessing import cpu_count
import os

def main(path_to_yml_file):
    spec = parse_yaml(path_to_yml_file)

    for _spec in spec['jobs']:
        scaper_mix(
            _spec['mixture_parameters'],
            _spec['sample_rate'],
            event_parameters=_spec['event_parameters'],
            coherent=_spec['coherent'],
            ref_db=_spec['ref_db'],
            bitdepth=_spec['bitdepth'],
            seed=_spec['seed'],
            num_workers=min(_spec['num_workers'], cpu_count())
        )

if __name__ == '__main__':
    parser = build_parser_for_yml_script()
    args = vars(parser.parse_args())
    main(args['spec'])