import sys
sys.path.insert(0, '.')

import os
from multiprocessing import cpu_count

from cookiecutter_repo.utils.parallel import parallel_process
from nussl import AudioSignal
import os
import glob
from multiprocessing import cpu_count
from runners.utils import build_parser_for_yml_script, parse_yaml

from argparse import ArgumentParser
import shutil
import yaml
import logging

audio_extensions = ['.wav', '.mp3', '.aac']

def resample_audio_file(original_path, resample_path, sample_rate):
    audio_signal = AudioSignal(original_path)
    resample = True

    if os.path.exists(resample_path):
        resampled_signal = AudioSignal(resample_path)
        resample = resampled_signal.sample_rate != sample_rate
    
    if resample:
        logging.info(
            f'{original_path} @ {audio_signal.sample_rate} -> {resample_path} @ {sample_rate}'
        )
        audio_signal.resample(sample_rate)
        audio_signal.write_audio_to_file(resample_path)

def ig_f(dir, files):
    return [f for f in files if os.path.isfile(os.path.join(dir, f))]

def main(path_to_yml_file):
    spec = parse_yaml(path_to_yml_file)

    for _spec in spec['jobs']:
        try:
            shutil.copytree(
                _spec['input_path'], 
                _spec['output_path'], 
                ignore=ig_f
            )
        except:
            pass

        input_audio_files = []
        for ext in audio_extensions:
            input_audio_files += glob.glob(
                f"{_spec['input_path']}/**/*{ext}", 
                recursive=True
            )

        output_audio_files = [
            x.replace(_spec['input_path'], _spec['output_path'])
            for x in input_audio_files
        ]
        arguments = [
            {
                'original_path': input_audio_files[i],
                'resample_path': output_audio_files[i][:-4] + '.wav',
                'sample_rate': _spec['sample_rate'],
            } 
            for i in range(len(input_audio_files))
        ]

        parallel_process(
            arguments, 
            resample_audio_file, 
            n_jobs=min(_spec['num_workers'], cpu_count()),
            front_num=1,
            use_kwargs=True,
        )

if __name__ == '__main__':
    parser = build_parser_for_yml_script()
    args = vars(parser.parse_args())
    main(args['spec'])