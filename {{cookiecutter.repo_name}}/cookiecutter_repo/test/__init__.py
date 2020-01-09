from nussl.evaluation.si_sdr import ScaleInvariantSDR
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import os
from .. import algorithms
import inspect
import copy
import logging

class EvaluationRunner(object):
    def __init__(
        self, 
        testers, 
        algorithm_config, 
        dataset, 
        max_workers=1,
        use_blocking_executor=False
    ):
        self.evaluation_executor = ProcessPoolExecutor(max_workers=max_workers)
        self.main_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.dataset = dataset
        self.testers = testers
        self.algorithm_config = algorithm_config
        self.use_blocking_executor = use_blocking_executor

        self.AlgorithmClass = getattr(algorithms, algorithm_config['class'])
        dummy_mixture = self.dataset.load_audio_files(self.dataset.files[0])[0]

        if self.use_blocking_executor:
            blocking_algorithm_config = copy.deepcopy(
                self.algorithm_config['args']
            )
            if 'use_cuda' in inspect.getargspec(AlgorithmClass).args:
                blocking_algorithm_config['use_cuda'] = True
                self.algorithm_config['args']['use_cuda'] = False
            self.blocking_algorithm = self.AlgorithmClass(
                dummy_mixture, **blocking_algorithm_config
            )
            self.blocking_executor = ThreadPoolExecutor(max_workers=1)

    def blocking_func(file_path):
        mixture, _, _ = self.dataset.load_audio_files(file_path)
        self.blocking_algorithm.set_audio_signal(mixture)
        self.blocking_algorithm._compute_spectrograms()
        features = self.blocking_algorithm.extract_features()
        logging.info(f'Features extracted for {file_path}')
        return {'features': features}

    def report_results(self, scores):
        results = compute_mean(scores)
        logging.info(
            f"SDR => {np.mean(results['SDR']):4.1f} | "
            f"SIR => {np.mean(results['SIR']):4.1f} | "
            f"SAR => {np.mean(results['SAR']):4.1f} | " 
        )

    def run_func(self, file_path, data=None):
        mixture, sources = self.dataset.load_audio_files(file_path)[0:2]
        
        algorithm = self.AlgorithmClass(mixture, **self.algorithm_config)
        for key in data:
            if key not in inspect.getargspec(algorithm.run):
                data.pop(key)

        algorithm.run(**data)
        estimates = algorithm.make_audio_signals()

        tester_args = {
            'true_sources_list': sources,
            'estimated_sources_list': estimates
        }

        for tester in self.testers:
            TestClass = tester[0]
            kwargs = tester[1]
            args = {}
            for k in tester_args:
                if k in inspect.getargspec(TestClass):
                    args[k] = tester_args[k]
            args.update(kwargs)
            evaluator = TestClass(**args)
            scores = evaluator.evaluate()
            self.report_results(scores)

        return

    def main_func(self, file_path):
        if self.use_blocking_executor:
            task = self.blocking_executor.submit(
                self.blocking_func, file_path
            )
            data = task.result()
        
        