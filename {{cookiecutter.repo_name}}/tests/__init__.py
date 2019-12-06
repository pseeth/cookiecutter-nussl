import comet_ml

import os
import sys

if os.getenv('NUSSL_DIRECTORY', None):
    sys.path.insert(0, os.getenv('NUSSL_DIRECTORY'))

from .test_data import _download_test_data
_download_test_data()