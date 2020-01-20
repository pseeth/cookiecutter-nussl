import os
from ..utils.parallel import parallel_process
from scaper import Scaper, generate_from_jams
import numpy as np
from tqdm import tqdm

import subprocess
import os
import logging
import copy

def make_one_mixture(sc, path_to_file, num_sources, event_parameters, allow_repeated_label):
    for j in range(num_sources):
        sc.add_event(**event_parameters)
    sc.generate(
        path_to_file, 
        path_to_file.replace('.wav', '.jams'), 
        no_audio=True,
        allow_repeated_label=allow_repeated_label
    )
    sc.fg_spec = []

def instantiate_and_get_event_spec(sc, master_label, scene_duration, event_parameters):
    sc.fg_spec = []
    _event_parameters = copy.deepcopy(event_parameters)
    _event_parameters['label'] = ('const', master_label)
    sc.add_event(**_event_parameters)
    event = sc._instantiate_event(sc.fg_spec[-1])
    sc.fg_spec = []
    return sc, event

def make_one_mixture_coherent(sc, path_to_file, labels, event_parameters, allow_repeated_label):
    sc, event = instantiate_and_get_event_spec(sc, labels[0], sc.duration, event_parameters)
    for label in labels:
        try:
            sc.add_event(
                label=('const', label),
                source_file=('const', event.source_file.replace(labels[0], label)),
                source_time=('const', event.source_time),
                event_time=('const', 0),
                event_duration=('const', sc.duration),
                snr=event_parameters['snr'],
                pitch_shift=('const', event.pitch_shift),
                time_stretch=('const', event.time_stretch)
            )
        except:
            logging.exception(f"Got an error for {label} @ {_source_file}. Moving on...")
    sc.generate(
        path_to_file, 
        path_to_file.replace('.wav', '.jams'), 
        no_audio=True, 
        allow_repeated_label=allow_repeated_label
    )
    sc.fg_spec = []

def synthesize_one_mixture(jams_file):
    wav_file = jams_file.replace('.jams', '.wav')
    generate_from_jams(jams_file, wav_file, save_sources=True)

def synthesize_mixtures_in_parallel(target_path, n_jobs):
    jam_files = [
        os.path.join(target_path, x) for x in os.listdir(target_path) if '.jams' in x
    ]
    parallel_process(
        jam_files, synthesize_one_mixture, n_jobs
    )

def scaper_mix(
    mixture_parameters, 
    sample_rate, 
    event_parameters=None,
    coherent=False,
    allow_repeated_label=False,
    ref_db=-40, 
    bitdepth=16,
    seed=0,
    num_workers=1,
):
    np.random.seed(seed)
    logging.info('Making JAMS files')

    for key, params in mixture_parameters.items():
        if 'event_parameters' in params:
            _event_parameters = params['event_parameters']
        else:
            _event_parameters = event_parameters

        # make sure all the vals in _event_parameters are tuples
        for key in _event_parameters:
            if _event_parameters[key]:
                _event_parameters[key] = tuple(_event_parameters[key])

        generators = []
        logging.info('Making generators')
        bg_path = params['background_path']
        if not bg_path:
            bg_path = params['foreground_path']
        for i in tqdm(range(params['num_mixtures'])):
            sc = Scaper(
                params['scene_duration'], 
                fg_path=params['foreground_path'], 
                bg_path=bg_path, 
                random_state=np.random.randint(params['num_mixtures']*10)
            )
            sc.ref_db = ref_db
            sc.sr = sample_rate
            sc.bitdepth = bitdepth
            generators.append(sc)

        os.makedirs(params['target_path'], exist_ok=True)
        
        timings = {}
        silent_files = {'default': True}

        if coherent:
            args = [
                {
                    'path_to_file': os.path.join(params['target_path'], f'{i:08d}.wav'),
                    'sc': generators[i],
                    'labels': params['labels'],
                    'event_parameters': _event_parameters,
                    'allow_repeated_label': allow_repeated_label
                } for i in range(params['num_mixtures'])
            ]
            mix_func = make_one_mixture_coherent
        else:
            args = [
                {
                    'path_to_file': os.path.join(params['target_path'], f'{i:08d}.wav'),
                    'sc': generators[i],
                    'num_sources': params['num_sources'],
                    'event_parameters': _event_parameters,
                    'allow_repeated_label': allow_repeated_label
                } for i in range(params['num_mixtures'])
            ]
            mix_func = make_one_mixture

        parallel_process(args, mix_func, n_jobs=num_workers, front_num=1, use_kwargs=True)

    logging.info(f'Synthesizing mixtures in parallel across {num_workers} threads')
    for key, params in mixture_parameters.items():
        synthesize_mixtures_in_parallel(params['target_path'], num_workers)