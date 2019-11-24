import sys
sys.path.insert(0, '.')

from cookiecutter_repo.dataset import scaper_mix
import logging
import yaml
from argparse import ArgumentParser
from multiprocessing import cpu_count
import os

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        'spec', 
        type=str, 
        help='Path to .yml file containing specification for dataset creation.'
    )
    args = vars(parser.parse_args())
    with open(args['spec'], 'r') as f:
        spec = yaml.load(f, Loader=yaml.FullLoader)

    for split in spec['mixture_parameters']:
        if isinstance(spec['mixture_parameters'][split], dict):
            for key in spec['mixture_parameters'][split]:
                if 'path' in key:
                    if spec['mixture_parameters'][split][key] is not None:
                        spec['mixture_parameters'][split][key] = (
                            os.path.join(os.getenv('DATA_DIRECTORY', ''),
                            spec['mixture_parameters'][split][key])
                        )

    scaper_mix(
        spec['mixture_parameters'],
        spec['sample_rate'],
        event_parameters=spec['event_parameters'],
        coherent=spec['coherent'],
        ref_db=spec['ref_db'],
        bitdepth=spec['bitdepth'],
        seed=spec['seed'],
        num_workers=min(spec['num_workers'], cpu_count())
    )