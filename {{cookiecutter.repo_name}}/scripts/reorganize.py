"""
Takes a folder with audio file structure that looks like this:
    folder_input/
        mixture_one_name/
            vocals.wav
            bass.wav
            drums.wav
            other.wav
        mixture_two_name/
            vocals.wav
            bass.wav
            drums.wav
            other.wav
        ...

and reorganizes it to a different folder like so:
    folder_output/
        vocals/
            mixture_one_name.wav
            mixture_two_name.wav
            ...
        bass/
            mixture_one_name.wav
            mixture_two_name.wav
            ...
        drums/
            mixture_one_name.wav
            mixture_two_name.wav
            ...
        other/
            mixture_one_name.wav
            mixture_two_name.wav
            ...
    
so that it can be processed easily by Scaper. Notably, MUSDB has this folder structure.
"""

import sys
sys.path.insert(0, '.')

import csv
import os
import shutil
from cookiecutter_repo.utils.parallel import parallel_process
from multiprocessing import cpu_count
from runners.utils import build_parser_for_yml_script, parse_yaml
import glob
import logging
from argparse import ArgumentParser
import yaml

def split_folder_by_class(path_to_file, output_directory):
    head, tail = os.path.split(path_to_file)
    class_name, ext = os.path.splitext(tail)
    head, mixture_name = os.path.split(head)

    output_path = os.path.join(output_directory, class_name, mixture_name + ext)
    os.makedirs(os.path.join(output_directory, class_name), exist_ok=True)

    if not os.path.exists(output_path):
        logging.info(f"{path_to_file} -> {output_path}")
        shutil.copyfile(path_to_file, output_path)

def main(path_to_yml_file):
    spec = parse_yaml(path_to_yml_file)

    for _spec in spec['jobs']:
        data_directory = _spec['input_path']
        output_directory = _spec['output_path']

        paths_to_files = glob.glob(f'{data_directory}/**/*.wav')
        args = [{
            'path_to_file': p,
            'output_directory': output_directory
        } for p in paths_to_files]

        parallel_process(
            args, 
            split_folder_by_class,
            n_jobs=cpu_count(), 
            front_num=1, 
            use_kwargs=True
        )

if __name__ == '__main__':
    parser = build_parser_for_yml_script()
    args = vars(parser.parse_args())
    main(args['spec'])