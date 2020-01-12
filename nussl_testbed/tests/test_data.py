from scripts import mix_with_scaper, reorganize, resample
from src import logging
from runners.utils import load_yaml
import os

os.environ['DATA_DIRECTORY'] = 'tests/out/_test_data/'

def test_data_musdb_reorganize():
    reorganize.main('data_prep/musdb/reorganize.yml')        

def test_data_musdb_resample():
    # Run it once to make sure it resamples everything.
    resample.main('data_prep/musdb/resample.yml')

    # Run it again to make sure it doesn't redo work if resampled file exists.
    resample.main('data_prep/musdb/resample.yml')

def test_data_musdb_coherent():
    mix_with_scaper.main('data_prep/musdb/coherent.yml')

def test_data_musdb_incoherent():
    mix_with_scaper.main('data_prep/musdb/incoherent.yml')

def test_data_wsj_incoherent():
    mix_with_scaper.main('data_prep/wsj/incoherent.yml')