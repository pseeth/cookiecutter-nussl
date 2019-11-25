import glob
from runners.utils import load_yaml    

def test_yaml():
    path_to_ymls = glob.glob('./**/*.yml')
    for path_to_yml in path_to_ymls:
        data = load_yaml(path_to_yml)
        print(path_to_yml, data)