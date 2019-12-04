from runners.utils import load_yaml
from cookiecutter_repo import train, dataset, model, logging
from cookiecutter_repo.utils import loaders, seed
import glob
import pytest

import sys, os
import torch
import shutil

seed(0)

logger = logging.getLogger()
os.makedirs('tests/out/_test_train/logs/', exist_ok=True)
fh = logging.FileHandler(f'tests/out/_test_train/logs/output.txt')
logger.addHandler(fh)

def _load_dataset(config, split):
    config['dataset_config']['overwrite_cache'] = True
    config['dataset_config']['cache'] = 'tests/out/_test_dataset/'
    config['dataset_config']['fraction_of_dataset'] = .1
    dset = loaders.load_dataset(
            config['datasets'][split]['class'],
            config['datasets'][split]['folder'],
            config['dataset_config'],
        )
    return dset

paths_to_yml = list(glob.glob('./experiments/**/*.yml', recursive=True))
configs = [
    load_yaml(path_to_yml)
    for path_to_yml in paths_to_yml
]

@pytest.mark.parametrize("config", configs, ids=paths_to_yml)
def test_dataset(config):
    for split in config['datasets']:
        dset = _load_dataset(config, split)
        dset[0]

@pytest.mark.parametrize("config", configs, ids=paths_to_yml)
def test_model(config):
    if 'model_config' in config:
        model = loaders.load_model(config['model_config'])

@pytest.mark.parametrize("config", configs, ids=paths_to_yml)
def test_model_and_dataset_match(config):
    device = (
        torch.device('cuda') 
        if torch.cuda.is_available()
        else torch.device('cpu')
    )
    if 'datasets' in config and 'model_config' in config:
        for split in config['datasets']:
            dset = _load_dataset(config, split)
            data = dset[0]
            for key in data:
                data[key] = torch.from_numpy(
                    data[key]
                ).unsqueeze(0).float().to(device)
            model_instance = loaders.load_model(config['model_config'])
            model_instance = model_instance.to(device)
            output = model_instance(data)

@pytest.mark.parametrize("config", [], ids=[])
def test_train(config):
    if 'train_config' in config:
        train_class = config['train_config'].pop('class')
        output_folder = config['train_config'].pop('output_folder')
        output_folder = 'tests/out/_test_train/'
        config['train_config']['num_epochs'] = 1

        TrainerClass = getattr(train, train_class)

        train_dataset = _load_dataset(config, 'train')
        val_dataset = _load_dataset(config, 'val')

        model_instance = loaders.load_model(config['model_config'])

        trainer = TrainerClass(
            output_folder,
            train_dataset,
            model_instance,
            config['train_config'],
            validation_data=val_dataset,
            use_tensorboard=True,
            experiment=None,
        )

        trainer.fit()