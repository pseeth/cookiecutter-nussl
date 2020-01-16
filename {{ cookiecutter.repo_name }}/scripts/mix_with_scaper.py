import sys
sys.path.insert(0, '.')

from src.dataset import scaper_mix
import logging
from runners.utils import build_parser_for_yml_script, parse_yaml
from argparse import ArgumentParser
from multiprocessing import cpu_count
import os

def main(path_to_yml_file):
    spec = parse_yaml(path_to_yml_file)

    for _spec in spec['jobs']:
        logging.info(_spec)
        scaper_mix(
            _spec['mixture_parameters'],
            _spec['sample_rate'],
            event_parameters=_spec.pop('event_parameters', None),
            coherent=_spec.pop('coherent', False),
            ref_db=_spec.pop('ref_db', -40),
            bitdepth=_spec.pop('bitdepth', 16),
            seed=_spec.pop('seed', 0),
            num_workers=min(_spec.pop('num_workers', 1), cpu_count()),
            allow_repeated_label=_spec.pop('allow_repeated_label', False),
        )

if __name__ == '__main__':
    parser = build_parser_for_yml_script()
    args = vars(parser.parse_args())
    main(args['spec'])