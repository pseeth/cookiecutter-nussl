import comet_ml

import os
import sys
import pytest

from scripts.download_toy_data import download_toy_data

@pytest.fixture(scope="session", autouse=True)
def setup_tests():
    download_toy_data('tests/out/_test_data/')