from multiprocessing import cpu_count
import GPUtil
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import random
import time

def job_runner(experiment, lock, run_experiment=True):
    try:
        logging.info(
            f'Processing {experiment.experiment_key} w/ run_experiment = {run_experiment}.'
        )
        if run_experiment:
            experiment.run()

        with lock:
            logging.info(f'{experiment.experiment_key} acquired a lock on Google Sheet')
            experiment.analyze()
            experiment.upload_to_gsheet()
    except:
        logging.exception('Got exception in uploading.')
    
    logging.info(f'{experiment.experiment_key} released a lock on Google Sheet')
    logging.info(f'Experiment {experiment.experiment_key} complete.')

class ExperimentRunnerPool(object):
    def __init__(self, max_workers=10, run_experiment=True):
        self.gpus = GPUtil.getGPUs()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.blocking_executor = ThreadPoolExecutor(max_workers=1)
        self.taken_gpus = []
        self.lock = threading.Lock()
        self.run_experiment = run_experiment

    def submit(self, experiments): 
        allocated_exps = []
        while len(allocated_exps) < len(experiments):
            taken_gpus = []
            num_gpus_allocated = 0
            for exp in experiments:
                if exp in allocated_exps:
                    continue
                logging.info(f'Trying to allocate resources for {exp.experiment_key}')
                num_gpus = int(exp.parameters['info']['num_gpus'])
                blocking = exp.parameters['info'].pop('blocking', False)
                available_gpus = GPUtil.getAvailable(order = 'first', limit=num_gpus + num_gpus_allocated,
                    maxLoad = 0.05, maxMemory = 0.05, includeNan=False, 
                    excludeID=[], excludeUUID=[]
                )
                logging.info(
                    f'Available GPUs: {available_gpus}'
                )
                for t in taken_gpus:
                    if t in available_gpus:
                        available_gpus.remove(t)
                if len(available_gpus) >= num_gpus:
                    logging.info(
                        f'Found GPUs {available_gpus} for {exp.experiment_key}' 
                        f'which needed {num_gpus} GPUs'
                    )
                    taken_gpus += available_gpus
                    
                    exp.parameters['info']['gpus'] = (
                        ','.join(map(str, available_gpus))
                    )

                    if blocking:
                        logging.info(f"Blocking requested. Submitting {exp.experiment_key} to blocking executor.")
                        self.blocking_executor.submit(
                            job_runner, exp, self.lock, run_experiment=self.run_experiment
                        )
                        allocated_exps.append(exp)
                        taken_gpus = []
                        self.blocking_executor.shutdown(wait=True)
                    else:
                        self.executor.submit(
                            job_runner, exp, self.lock, run_experiment=self.run_experiment
                        )
                        allocated_exps.append(exp)
                        num_gpus_allocated = len(taken_gpus)

            if len(allocated_exps) < len(experiments):
                logging.info(f"{len(experiments)} experiments remaining. Trying again in 1 minute...")
                time.sleep(5)
        
        self.executor.shutdown(wait=True)