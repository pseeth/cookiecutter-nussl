from scripts import pipeline
import os
import pytest

os.environ['DATA_DIRECTORY'] = 'tests/out/_test_data/'

pipeline_ymls = ['data_prep/musdb/pipeline.yml']
@pytest.mark.parametrize("path_to_yml", pipeline_ymls, ids=pipeline_ymls)
def test_pipeline(path_to_yml):
    pipeline.main(path_to_yml)