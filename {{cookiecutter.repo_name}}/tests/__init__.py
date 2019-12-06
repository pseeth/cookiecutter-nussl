import comet_ml

import os
import sys

if os.getenv('NUSSL_DIRECTORY', None):
    sys.path.insert(0, os.getenv('NUSSL_DIRECTORY'))

from scripts.download_toy_data import download_toy_data
download_toy_data('tests/out/_test_data/')