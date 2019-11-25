import glob
import yaml

def _parse_yaml(path_to_yml):
    with open(path_to_yml, 'r') as f:
        spec = yaml.load(f, Loader=yaml.FullLoader)
    print(spec)

def test_yaml():
    path_to_ymls = glob.glob('./**/*.yml')
    for path_to_yml in path_to_ymls:
        _parse_yaml(path_to_yml)