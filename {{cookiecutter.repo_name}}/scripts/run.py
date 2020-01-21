from . import cmd, document_parser
from argparse import ArgumentParser
import subprocess
import logging

def run(command, run_in='host'):
    """
    Runs a command in the shell. Useful for sequences like wget a dataset, then
    unzip to another directory. You can just put the command in a yml file and
    call it here. You can run a sequence of commands easily by putting them one
    after the other in a .yml file and calling this script with the '-y' option.
    
    Args:
        command (str): Command to run
    """
    logging.info(command)
    subprocess.run(
        [
            f"""
            make run_in_{run_in} command="{command}"
            """
        ], 
        shell=True,
    )

@document_parser('run', 'scripts.run.run')
def build_parser():
    parser = ArgumentParser()
    parser.add_argument(
        '--command',
        required=True,
        type=str,
        help='Command to run.'
    )
    parser.add_argument(
        '--run_in',
        required=False,
        default='host',
        type=str,
        help='Whether to run the command in the host or the container. Defaults to host.'
    )
    return parser

if __name__ == "__main__":
    cmd(run, build_parser)