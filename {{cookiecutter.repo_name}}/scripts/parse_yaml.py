from argparse import ArgumentParser
import yaml

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'spec', 
        type=str, 
        help='Path to .yml file to parse.'
    )
    args = vars(parser.parse_args())
    with open(args['spec'], 'r') as f:
        spec = yaml.load(f, Loader=yaml.FullLoader)
    print(spec)