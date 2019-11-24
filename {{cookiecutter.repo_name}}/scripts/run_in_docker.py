#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

from runners import DockerRunner
from argparse import ArgumentParser
import subprocess

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('command', type=str, nargs='+', help='command to run in docker')
    parser.add_argument('--gpus', type=str, default='')
    parser.add_argument('--name', type=str, default=None)
    args = vars(parser.parse_args())
    if len(args['command']) == 1:
        args['command'] = args['command'][0].split(' ')

    runner = DockerRunner()
    name = runner.run(args['command'], args['gpus'], args['name'])
    subprocess.call(['docker', 'logs', '-f', name])