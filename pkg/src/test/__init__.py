from nussl.evaluation.si_sdr import ScaleInvariantSDR
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import os
from .. import algorithms
import inspect
import copy
import logging
import numpy as np
import yaml

class EvaluationRunner(object):
    def __init__(
        self, 
        testers, 
        algorithm_config, 
        dataset,
        output_path,
        max_workers=1,
        use_blocking_executor=False
    ):
        self.evaluation_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.main_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.dataset = dataset
        self.testers = testers
        self.algorithm_config = algorithm_config
        self.use_blocking_executor = use_blocking_executor

        self.output_path = os.path.join(output_path, 'results')
        os.makedirs(self.output_path, exist_ok=True)

        self.AlgorithmClass = getattr(algorithms, algorithm_config['class'])
        dummy_mixture = self.dataset.load_audio_files(self.dataset.files[0])[0]

        if self.use_blocking_executor:
            blocking_algorithm_config = copy.deepcopy(
                self.algorithm_config['args']
            )
            if 'use_cuda' in inspect.getargspec(self.AlgorithmClass).args:
                blocking_algorithm_config['use_cuda'] = True
                self.algorithm_config['args']['use_cuda'] = False
            self.blocking_algorithm = self.AlgorithmClass(
                dummy_mixture, **blocking_algorithm_config
            )
            self.blocking_executor = ThreadPoolExecutor(max_workers=1)

    def blocking_func(self, file_path):
        mixture, _, _ = self.dataset.load_audio_files(file_path)
        self.blocking_algorithm.set_audio_signal(mixture)
        self.blocking_algorithm._compute_spectrograms()
        features = self.blocking_algorithm.extract_features()
        logging.info(f'Features extracted for {file_path} of shape {features.shape}')
        return {'features': features}

    def log_scores(self, scores):
        for key in scores:
            if key != 'permutation':
                logging_str = f"{key}: "
                for metric in scores[key]:
                    logging_str += f"{metric} => {np.mean(scores[key][metric])}, "
                logging.info(logging_str)
    
    def run_func(self, file_path, data=None):
        mixture, sources = self.dataset.load_audio_files(file_path)[0:2]
        algorithm = self.AlgorithmClass(mixture, **self.algorithm_config['args'])
        if data:
            for key in data:
                if key not in inspect.getargspec(algorithm.run).args:
                    data.pop(key)
            algorithm.run(**data)
        else:
            algorithm.run()
        estimates = algorithm.make_audio_signals()

        tester_args = {
            'true_sources_list': sources,
            'estimated_sources_list': estimates
        }

        all_scores = []
        try:
            for tester in self.testers:
                TestClass = tester[0]
                kwargs = tester[1]
                args = {}
                for k in tester_args:
                    if k in inspect.getargspec(TestClass).args:
                        args[k] = tester_args[k]
                        
                args.update(kwargs)
                evaluator = TestClass(**args)
                scores = evaluator.evaluate()
                self.log_scores(scores)
                all_scores.append(scores)

            path_to_yml = os.path.join(
                self.output_path, 
                os.path.splitext(os.path.basename(file_path))[0] + '.yml'
            )
            logging.info(path_to_yml)
            with open(path_to_yml, 'w') as f:
                yaml.dump(all_scores, f)
        except:
            logging.exception()

    def main_func(self, file_path):
        data = None
        if self.use_blocking_executor:
            task = self.blocking_executor.submit(
                self.blocking_func, file_path
            )
            data = task.result()

        self.evaluation_executor.submit(
            self.run_func, file_path, data
        )

    def run(self):
        for file_path in self.dataset.files:
            self.main_executor.submit(self.main_func, file_path)

        self.main_executor.shutdown(wait=True)
        self.evaluation_executor.shutdown(wait=True)