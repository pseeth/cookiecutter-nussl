import csv
import os
import shutil
from src.utils.parallel import parallel_process
from multiprocessing import cpu_count
from runners.utils import load_yaml, parse_yaml
from . import cmd, document_parser
import glob
import logging
import argparse
import yaml
import sys

def split_urbansound_by_fold(path_to_file, output_directory, make_copy=False, 
    train_folds=[1, 2, 3, 4, 5, 6, 7, 8], val_folds=[9], test_folds=[10],
    path_to_urbansound_csv=None):
    """
    Reorganizes the urbansound dataset using the metadata/UrbanSound8K.csv to 
    determine which fold each file belongs to. It makes symlinks in the corresponding
    train, test, and val folders.
    
    Args:
        path_to_file (str): Path to the audio file that will be reorganized. Has form
            /path/to/mixture_name/source_name.ext
        output_directory (str): Where the file after swapping the mixture_name and source_name
            will be copied to.
        use_symlink (bool, optional): Whether to use a symlink or to actually copy the file. 
            Defaults to True.
        train_folds (list, optional): Which folds belong to the train set. 
            Defaults to [1, 2, 3, 4, 5, 6, 7, 8].
        val_folds (list, optional): Which folds belong to the validation set. 
            Defaults to [9].
        test_folds (list, optional): Which folds belong to the test set. 
            Defaults to [10].
        path_to_urbansound_csv ([type]): Path to metadata/UrbanSound8k.csv. 
            Defaults to None.
    
    Raises:
        ValueError: raises an error if the path to the csv isn't given.
    """
    raise NotImplementedError()

    if not path_to_urbansound_csv:
        raise ValueError("Path to urban sound CSV must be specified!")

    # Below doesn't work yet, just copying from the old stuff.
    for d in ['train', 'validation', 'test']:
        os.makedirs(
            os.path.join(data_directory, 'data', d),
            exist_ok=True)

    def copy_audio_to_folder_of_class(row):
        target_directory = data_directory
        class_name = row['class']
        source_file = os.path.join(data_directory, 'audio', f"fold{row['fold']}", row['slice_file_name'])
        if int(row['fold']) in train_folds:
            target_directory = os.path.join(target_directory, 'train', class_name)
        elif int(row['fold']) in val_folds:
            target_directory = os.path.join(target_directory, 'validation', class_name)
        else:
            target_directory = os.path.join(target_directory, 'test', class_name)

        os.makedirs(target_directory, exist_ok=True)
        target_file = os.path.join(target_directory, row['slice_file_name'])

        print(f"Copying {source_file} w/ fold {row['fold']} to {target_file}", flush=True)
        shutil.copyfile(source_file, target_file)


    with open(os.path.join(data_directory, 'metadata', 'UrbanSound8K.csv'), 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

def split_folder_by_class(path_to_file, output_directory, make_copy=False):
    """Splits a folder by class which is indicated by the name of the file. 
    
    The mixture name is the name of the parent directory to the file. This function
    is used to organize datasets like musdb for consumption by Scaper for mixing
    new datasets.

    Takes a folder with audio file structure that looks like this::
    
        folder_input/
            mixture_one_name/
                vocals.wav
                bass.wav
                drums.wav
                other.wav
            mixture_two_name/
                vocals.wav
                bass.wav
                drums.wav
                other.wav
            ...

    and reorganizes it to a different folder like so::

        folder_output/
            vocals/
                mixture_one_name.wav
                mixture_two_name.wav
                ...
            bass/
                mixture_one_name.wav
                mixture_two_name.wav
                ...
            drums/
                mixture_one_name.wav
                mixture_two_name.wav
                ...
            other/
                mixture_one_name.wav
                mixture_two_name.wav
                ...
        
    so that it can be processed easily by Scaper. Notably, MUSDB has this folder 
    structure. This reorganization is done via symlinks so that the entire dataset
    is not copied.

    Args:
        path_to_file (str): Path to the audio file that will be reorganized. Has form
            /path/to/mixture_name/source_name.ext
        output_directory (str): Where the file after swapping the mixture_name and source_name
            will be copied to.
        use_symlink (bool): Whether to use a symlink or to actually copy the file. 
            Defaults to True.
    """
    head, tail = os.path.split(path_to_file)
    class_name, ext = os.path.splitext(tail)
    head, mixture_name = os.path.split(head)

    output_path = os.path.join(output_directory, class_name, mixture_name + ext)
    os.makedirs(os.path.join(output_directory, class_name), exist_ok=True)

    if not os.path.exists(output_path):
        logging.info(f"{path_to_file} -> {output_path}")
        if make_copy:
            shutil.copyfile(path_to_file, output_path)
        else:
            os.symlink(path_to_file, output_path)

def reorganize(input_path, output_path, org_func, make_copy=False, 
               audio_extensions=['.wav', '.mp3', '.aac'], **kwargs):
    """
    Reorganizes the folders in the input path into the output path given an 
    organization function, passed in by org_func.

    Args:
        input_path (str): Root of folder where all audio files will be reorganized.
        output_path (str): Root of folder where the reorganized files will be placed. 
        org_func (str): Organization function to use reorganize the dataset. Should 
            correspond to the name of a function in reorganize.py.
        use_symlink (bool): Whether to use a symlink or to actually copy the file. 
            Defaults to True.
        audio_extensions (list, optional): Audio extensions to look for in the 
            input_path. Matching ones will be reorganize and placed into the output 
            directory via a symlink.. Defaults to ['.wav', '.mp3', '.aac'].
        kwargs (dict): Additional keyword arguments that are passed to the org_func
            that is specified.
    """
    paths_to_files = []
    for ext in audio_extensions:
        paths_to_files += glob.glob(f'{input_path}/**/*{ext}')

    args = [{
        'path_to_file': p,
        'output_directory': output_path,
        'make_copy': make_copy,
        **kwargs
    } for p in paths_to_files]

    module = sys.modules[__name__]
    org_func = getattr(module, org_func)

    parallel_process(
        args, 
        org_func,
        n_jobs=cpu_count(), 
        front_num=1, 
        use_kwargs=True
    )

@document_parser('reorganize', 'scripts.reorganize.reorganize')
def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_path', type=str, 
        help="""Root of folder where all audio files will be reorganized."""
    )
    parser.add_argument(
        '--output_path', type=str, 
        help="""Root of folder where all reorganized files will be placed."""
    )
    parser.add_argument(
        '--org_func', type=str,
        help="""Organization function to use reorganize the dataset. Should correspond
        to the name of a function in reorganize.py."""
    )
    parser.add_argument(
        '--make_copy', 
        action="store_true",
        help="""Whether to use a symlink or to actually copy the file.""",
    )
    parser.add_argument(
        '--audio_extensions', nargs='+', 
        help="""Audio extensions to look for in the input_path. Matching ones will
        be reorganize and placed into the output directory via a symlink.""",
        default=['.wav', '.mp3', '.aac']
    )
    return parser

if __name__ == '__main__':
    cmd(reorganize, build_parser)