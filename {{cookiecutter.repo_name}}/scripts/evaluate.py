from runners.experiment_utils import load_experiment, save_experiment
from src import dataset, test, model
from src.utils import loaders, seed
import logging
from runners.utils import load_yaml
from . import cmd, document_parser
from argparse import ArgumentParser
import os

def evaluate(path_to_yml_file, eval_keys=['test']):
    """
    Evaluates an experiment across all of the data for each key in eval_keys. The key
    must correspond to a dataset included in the experiment configuration. This uses
    :py:class:`src.test.EvaluationRunner` to evaluate the performance of the model on
    each dataset.
    
    Args:
        path_to_yml_file (str): Path to the yml file that defines the experiment. The
            corresponding test configuration for the experiment will be used to evaluate
            the experiment across all of the audio files in the test dataset.
        eval_keys (list): All of the keys to be used to evaluate the experiment. Will
            run the evaluation on each eval_key in sequence. Defaults to ['test'].
    """
    config, exp, path_to_yml_file = load_experiment(path_to_yml_file)

    if 'seed' in config['test_config']:
        seed(config['test_config']['seed'])

    if 'test' not in config['datasets']:
        logging.error('Test dataset must be specified!')
    
    test_classes = config['test_config']['testers']
    testers = []
    for key in test_classes:
        TestClass = getattr(test, key)
        args = test_classes[key]
        testers.append((TestClass, args))

    _datasets = {}

    for key in eval_keys:
        if key in config['datasets']:
            _datasets[key] = loaders.load_dataset(
                config['datasets'][key]['class'],
                config['datasets'][key]['folder'],
                config['dataset_config']
            )
        else:
            _datasets[key] = None

    for key in eval_keys:
        _tester = test.EvaluationRunner(
            testers,
            config['algorithm_config'],
            _datasets[key],
            config['info']['output_folder'],
            max_workers=config['test_config']['num_workers'],
            use_blocking_executor=config['test_config']['use_blocking_executor'],
        )
        _tester.run()

@document_parser('evaluate', 'scripts.evaluate.evaluate')
def build_parser():
    """
    Builds the parser for the evaluate script. See the arguments to 
    :py:func:`scripts.evaluate.evaluate`.

    Returns:
        :class:`argparse.ArgumentParser`: The parser for this script.
    """
    parser = ArgumentParser()
    parser.add_argument(
        "-p",
        "--path_to_yml_file",
        type=str,
        required=True,
        help="""Path to the configuration for the experiment that is getting evaluated. The
            corresponding test configuration for the experiment will be used to evaluate
            the experiment across all of the audio files in the test dataset.
        """
    )
    parser.add_argument(
        "-e",
        "--eval_keys",
        nargs='+',
        type=str,
        default=['test'],
        help="""All of the keys to be used to evaluate the experiment. Will
        run the evaluation on each eval_key in sequence. Defaults to ['test'].
        """
    )
    return parser

if __name__ == '__main__':
    cmd(evaluate, build_parser)