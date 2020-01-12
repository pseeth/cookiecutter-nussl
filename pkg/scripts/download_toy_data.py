import sys
sys.path.insert(0, '.')

from runners.utils import build_parser_for_yml_script, load_yaml
import os
from nussl import efz_utils
import zipfile

def download_toy_data(target_folder):
    def _unzip(path_to_zip, target_path):
        with zipfile.ZipFile(path_to_zip, 'r') as zip_ref:
            zip_ref.extractall(target_path)

    os.makedirs(target_folder, exist_ok=True)

    wsj_data = efz_utils.download_benchmark_file('babywsj_oW0F0H9.zip')
    _unzip(wsj_data, target_folder)

    musdb_data = efz_utils.download_benchmark_file('babymusdb.zip')
    _unzip(musdb_data, target_folder)

if __name__ == "__main__":
    parser = build_parser_for_yml_script()
    args = vars(parser.parse_args())
    config = load_yaml(args['spec'])
    download_toy_data(config['target_folder'])