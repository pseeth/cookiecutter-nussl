from runners.experiment_utils import load_experiment, save_experiment
from runners.utils import build_parser_for_yml_script
from src import logging
import os
import glob
import pytest

paths_to_yml = list(glob.glob('./experiments/**/*.yml', recursive=True))

@pytest.mark.parametrize("path_to_yml", paths_to_yml, ids=paths_to_yml)
def test_with_comet(path_to_yml):
    os.environ['ARTIFACTS_DIRECTORY'] = 'tests/out/_test_experiment_utils/'
    config, exp, path_to_yml_file = load_experiment(path_to_yml)
    save_experiment(config, exp)

@pytest.mark.parametrize("path_to_yml", paths_to_yml, ids=paths_to_yml)
def test_without_comet(path_to_yml):
    api_key = os.environ.pop('COMET_API_KEY', None)
    config, exp, path_to_yml = load_experiment(path_to_yml)     
    save_experiment(config, exp)
    if api_key:
        os.environ['COMET_API_KEY'] = api_key 

    # Test that it doesn't make a new experiment the second time around.
    load_experiment(path_to_yml)