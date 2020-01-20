import glob
from runners.utils import load_yaml   
import pytest 

@pytest.mark.parametrize(
    "path_to_yml",
     list(glob.glob('./**/*.yml', recursive=True)),
     ids=list(glob.glob('./**/*.yml', recursive=True))
)
def test_yaml(path_to_yml):
    data = load_yaml(path_to_yml)