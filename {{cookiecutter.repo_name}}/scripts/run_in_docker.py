#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

from runners import DockerRunner
from argparse import ArgumentParser
import subprocess
import os

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('command', type=str, nargs='+', help='command to run in docker')
    parser.add_argument('--name', type=str, default=None)
    parser.add_argument('--gpus', type=str, default='')
    args = vars(parser.parse_args())
    if len(args['command']) == 1:
        args['command'] = args['command'][0].split(' ')

    runner = DockerRunner()
    gpus = os.getenv('CUDA_VISIBLE_DEVICES', "")
    name = os.getenv('NAME', "")
    name = runner.run(args['command'], gpus, name)
    subprocess.call(['docker', 'logs', '-f', name])