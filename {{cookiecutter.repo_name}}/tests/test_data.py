from nussl import efz_utils
from scripts import mix_with_scaper, reorganize, resample
from cookiecutter_repo import logging
import zipfile
import os
from runners.utils import load_yaml

os.environ['DATA_DIRECTORY'] = 'tests/out/_test_data/'

def _unzip(path_to_zip, target_path):
    with zipfile.ZipFile(path_to_zip, 'r') as zip_ref:
        zip_ref.extractall(target_path)

def _download_test_data():
    os.makedirs('tests/out/_test_data/', exist_ok=True)

    wsj_data = efz_utils.download_benchmark_file('babywsj_oW0F0H9.zip')
    _unzip(wsj_data, 'tests/out/_test_data/')

    musdb_data = efz_utils.download_benchmark_file('babymusdb.zip')
    _unzip(musdb_data, 'tests/out/_test_data/')

def test_data_musdb_reorganize():
    _download_test_data()
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