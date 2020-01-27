from src.utils import loaders
from src import algorithms
from . import cmd, document_parser
from runners.experiment_utils import load_experiment
import inspect
import numpy as np
import os
import matplotlib.pyplot as plt
from argparse import ArgumentParser
import logging

def visualize(path_to_yml_file, file_names=[], eval_keys=['test']):
    """
    Takes in a path to a yml file containing an experiment configuration and runs
    the algorithm specified in the experiment on a random file from the test
    dataset specified in the experiment. If the algorithm has plotting available, then
    plot is used to visualize the algorithm and save it to a figure. The associated
    audio is also saved.
    
    Args:
        path_to_yml_file (str): Path to the yml file that defines the experiment. The 
            visualization will be placed into a "viz" folder in the same directory
            as the yml file.
        eval_keys (list): All of the dataset keys to be used to visualize the experiment. 
            Will visualize for each eval_key in sequence. Defaults to ['test'].
    """
    config, exp, path_to_yml_file = load_experiment(path_to_yml_file)
    algorithm_config = config['algorithm_config']
    AlgorithmClass = getattr(algorithms, algorithm_config['class'])
    _datasets = {}

    for key in eval_keys:
        if key in config['datasets']:
            _datasets[key] = loaders.load_dataset(
                config['datasets'][key]['class'],
                config['datasets'][key]['folder'],
                config['dataset_config']
            )

    for key in _datasets:
        i = np.random.randint(len(_datasets[key]))
        file_names = file_names if file_names else [_datasets[key].files[i]]

        for file_name in file_names:
            try:
                logging.info(f'Visualizing {file_name}')
                folder = os.path.splitext(os.path.basename(file_name))[0]
                output_folder = os.path.join(
                    config['info']['output_folder'], 'viz', key, folder)
                os.makedirs(output_folder, exist_ok=True)


                mixture = _datasets[key].load_audio_files(file_name)[0]

                logging.info(mixture)
                
                _algorithm = AlgorithmClass(mixture, **algorithm_config['args'])
                _algorithm.run()
                estimates = _algorithm.make_audio_signals()

                try:
                    plt.figure(figsize=(20, 10))
                    _algorithm.plot()
                    plt.savefig(
                        os.path.join(output_folder, 'viz.png'), bbox_inches='tight', dpi=100)
                except:
                    logging.error('Unable to plot.')

                mixture.write_audio_to_file(
                    os.path.join(output_folder, f'mixture.wav')
                )
                for i, e in enumerate(estimates):
                    e.write_audio_to_file(
                        os.path.join(output_folder, f'source{i}.wav')
                    )
            except:
                logging.error('File name not found.')


@document_parser('visualize', 'scripts.visualize.visualize')
def build_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "-p",
        "--path_to_yml_file",
        type=str,
        required=True,
        help="""Path to the yml file that defines the experiment. The 
            visualization will be placed into a "viz" folder in the same directory
            as the yml file.
        """
    )
    parser.add_argument(
        "-f",
        "--file_names",
        nargs='+',
        type=str,
        help="""Files to evaluate. Use only the base name of each file in the list that
            is being evaluated.
        """
    )
    parser.add_argument(
        "-e",
        "--eval_keys",
        nargs='+',
        type=str,
        default=['test'],
        help="""All of the dataset keys to be used to visualize the experiment. 
            Will visualize for each eval_key in sequence. Defaults to ['test'].
        """
    )
    return parser
    

if __name__ == '__main__':
    cmd(visualize, build_parser)
