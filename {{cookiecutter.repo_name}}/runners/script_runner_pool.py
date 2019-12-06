from multiprocessing import cpu_count
import GPUtil
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import random
import time
from .utils import prepare_script_args, disp_script
import subprocess

def job_runner(script):
    disp_script(script)
    
    try:
        if script['run_in'] == 'container':
            target = 'run_in_container'
        else:
            target = 'run_in_host'
        
        command = f"python {script['script']} {script['config']}"
        subprocess.run(
            [
                f"""
                make {target} command="{command}" gpus={script['allocated_gpus']}
                """
            ], 
            shell=True,
        )
    except:
        logging.exception('Got an exception running a script.')

    
class ScriptRunnerPool(object):
    """Class for launching scripts in sequence or parallel with corresponding 
    arguments. Keeps track of GPU resources for allocating jobs, takes care of
    blocking on certain jobs (e.g. dataset generation), and so on. Called by
    scripts/pipeline.yml or by 'make pipeline yml=path/to/.yml'.
    """
    def __init__(self, max_workers=10):
        self.gpus = GPUtil.getGPUs()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.blocking_executor = ThreadPoolExecutor(max_workers=1)
        self.taken_gpus = []

    def submit(self, scripts): 
        allocated_scripts = []
        while len(allocated_scripts) < len(scripts):
            taken_gpus = []
            num_gpus_allocated = 0
            for script in scripts:
                script = prepare_script_args(script)

                if script in allocated_scripts:
                    continue
                logging.info(f'Trying to allocate resources...')
                num_gpus = int(script['num_gpus'])
                
                available_gpus = GPUtil.getAvailable(
                    order = 'first', limit=num_gpus + num_gpus_allocated,
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
                        f"Found GPUs {available_gpus} for {script['config']} "
                        f"which needed {num_gpus} GPUs"
                    )
                    taken_gpus += available_gpus
                    script['allocated_gpus'] = ','.join(map(str, available_gpus))

                    if script['blocking']:
                        logging.info(
                            f"Blocking requested. Submitting {script['config']} " 
                            f"to blocking executor.")
                        self.blocking_executor.submit(job_runner, script)
                        allocated_scripts.append(script)
                        taken_gpus = []
                        self.blocking_executor.shutdown(wait=True)
                        self.blocking_executor = ThreadPoolExecutor(max_workers=1)
                    else:
                        self.executor.submit(job_runner, script)
                        allocated_scripts.append(script)
                        num_gpus_allocated = len(taken_gpus)

            if len(allocated_scripts) < len(scripts):
                logging.info(f"{len(scripts)} scripts remaining. Trying again soon...")
                time.sleep(5)
        
        self.executor.shutdown(wait=True)