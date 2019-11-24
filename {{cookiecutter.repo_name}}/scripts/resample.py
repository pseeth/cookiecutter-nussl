import sys
sys.path.insert(0, '.')

from multiprocessing import cpu_count
import os

from cookiecutter_repo.utils.parallel import parallel_process
from nussl import AudioSignal
import os
import glob
from multiprocessing import cpu_count

from argparse import ArgumentParser
import shutil
import yaml
import logging

def resample_audio_file(original_path, resample_path, sample_rate):
    logging.info(f'{original_path} -> {resample_path} @ {sample_rate}')
    audio_signal = AudioSignal(original_path)
    audio_signal.resample(sample_rate)
    audio_signal.write_audio_to_file(resample_path)

def ig_f(dir, files):
    return [f for f in files if os.path.isfile(os.path.join(dir, f))]

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'spec', 
        type=str, 
        help='Path to .yml file containing specification for downsampling.'
    )
    args = vars(parser.parse_args())
    with open(args['spec'], 'r') as f:
        spec = yaml.load(f, Loader=yaml.FullLoader)

    for key in spec:
        if 'path' in key:
            if spec[key] is not None:
                spec[key] = (
                    os.path.join(os.getenv('DATA_DIRECTORY', ''),
                    spec[key])
                )
    print(spec)

    try:
        shutil.copytree(
            spec['input_path'], 
            spec['output_path'], 
            ignore=ig_f
        )
    except:
        pass

    input_audio_files = glob.glob(f"{spec['input_path']}/**/*.wav", recursive=True)
    output_audio_files = [
        x.replace(spec['input_path'], spec['output_path']) 
        for x in input_audio_files
    ]
    arguments = [
        {
            'original_path': input_audio_files[i],
            'resample_path': output_audio_files[i],
            'sample_rate': spec['sample_rate'],
        } 
        for i in range(len(input_audio_files))
    ]

    parallel_process(
        arguments, 
        resample_audio_file, 
        n_jobs=min(spec['num_workers'], cpu_count()),
        front_num=1,
        use_kwargs=True,
    )