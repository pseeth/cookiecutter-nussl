import sys
sys.path.insert(0, '.')

from multiprocessing import cpu_count
import os

from cookiecutter_repo.utils.parallel import parallel_process
import librosa
from tqdm import tqdm
import sox
from nussl import AudioSignal
import os
import glob
import argparse

from argparse import ArgumentParser
import shutil

def downsample_audio_file(original_path, resample_path, sample_rate):
    print(f'{original_path} -> {resample_path} @ {sample_rate}', flush=True)
    audio_signal = AudioSignal(original_path)
    audio_signal.resample(sample_rate)
    audio_signal.write_audio_to_file(resample_path)

def ig_f(dir, files):
    return [f for f in files if os.path.isfile(os.path.join(dir, f))]

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-i', '--input_directory', type=str)
    parser.add_argument('-o', '--output_directory', type=str)
    parser.add_argument('-n', '--num_workers', type=int, default=1)
    parser.add_argument('-r', '--sample_rate', type=int, default=16000)
    args = vars(parser.parse_args())

    try:
        shutil.copytree(
            args['input_directory'], 
            args['output_directory'], 
            ignore=ig_f
        )
    except:
        pass

    input_audio_files = glob.glob(f"{args['input_directory']}/**/*.wav", recursive=True)
    output_audio_files = [
        x.replace(args['input_directory'], args['output_directory']) 
        for x in input_audio_files
    ]
    arguments = [
        {
            'original_path': input_audio_files[i],
            'resample_path': output_audio_files[i],
            'sample_rate': args['sample_rate'],
        } 
        for i in range(len(input_audio_files))
    ]

    parallel_process(
        arguments, 
        downsample_audio_file, 
        n_jobs=args['num_workers'], 
        front_num=1,
        use_kwargs=True,
    )