from runners.utils import load_yaml
from . import cmd, document_parser
import os
from nussl import efz_utils
import zipfile
from argparse import ArgumentParser

def download_toy_data(target_folder):
    """
    Downloads toy data to a target folder for the purposes of running some
    demo scripts.
    
    Args:
        target_folder (str): Where to put the data that gets downloaded.
    """
    def _unzip(path_to_zip, target_path):
        with zipfile.ZipFile(path_to_zip, 'r') as zip_ref:
            zip_ref.extractall(target_path)

    os.makedirs(target_folder, exist_ok=True)

    wsj_data = efz_utils.download_benchmark_file('babywsj_oW0F0H9.zip')
    _unzip(wsj_data, target_folder)

    musdb_data = efz_utils.download_benchmark_file('babymusdb.zip')
    _unzip(musdb_data, target_folder)

@document_parser('download_toy_data', 'scripts.download_toy_data.download_toy_data')
def build_parser():
    parser = ArgumentParser()
    parser.add_argument(
        '--target_folder',
        required=True,
        type=str,
        help='Folder where the toy data gets saved to.'
    )
    return parser

if __name__ == "__main__":
    cmd(download_toy_data, build_parser)