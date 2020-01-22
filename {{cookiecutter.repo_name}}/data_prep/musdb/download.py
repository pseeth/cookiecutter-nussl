import musdb
import os
from argparse import ArgumentParser

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--target_folder', required=True, type=str, 
        help="Where the MUSDB dataset gets stored to.")
    args = parser.parse_args()
    args = vars(args)
    mus = musdb.DB(root=args['target_folder'], download=True)


