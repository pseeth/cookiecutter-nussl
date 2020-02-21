import subprocess
import logging
from rq import Queue, Connection
from rq.job import Job
from redis import Redis
import GPUtil
import os
from time import sleep

timeout = 2e6 # 23 days, for getting around RQ's quirks.

def allocate_resources_and_queue(command, name=None, depends_on=None, num_gpus=0, 
                               blocking=False, redis_path='redis.sock'):
    with Connection(Redis(unix_socket_path=redis_path)):
        _queue = Queue('blocking') if blocking else None
        allocated_gpus = ''
        meta = {}

        not_allocated = True

        if _queue is None:
            if num_gpus > 0:
                _queue = Queue('gpu')
            else:
                _queue = Queue('cpu')

        while not_allocated:
            if num_gpus > 0:
                available_gpus = GPUtil.getAvailable(
                    order = 'first', limit=1000,
                    maxLoad = 0.05, maxMemory = 0.05, includeNan=False, 
                    excludeID=[], excludeUUID=[]
                )

                q_gpu = Queue('gpu')
                q_blocking = Queue('blocking')

                registry = q_gpu.started_job_registry
                blocking_registry = q_blocking.started_job_registry
                other_job_gpus = []
                for job_id in registry.get_job_ids() + blocking_registry.get_job_ids():
                    _job = Job.fetch(job_id)
                    if 'gpu' in _job.meta:
                        if isinstance(_job.meta['gpu'], list):
                            other_job_gpus.extend(_job.meta['gpu'])
                        else:
                            other_job_gpus.append(_job.meta['gpu'])            
                
                available_gpus = [a for a in available_gpus if a not in other_job_gpus]

                if len(available_gpus) >= num_gpus:
                    available_gpus = available_gpus[:num_gpus]
                    allocated_gpus = ','.join(map(str, available_gpus))
                    meta = {'gpu': available_gpus}
                    not_allocated = False
                else:
                    logging.info('Unable to allocate resources...Trying again in 30 seconds.')
                    sleep(30)
            else:
                not_allocated = False

        command = f'export CUDA_VISIBLE_DEVICES={allocated_gpus} && {command}'
        _queue.enqueue(
            subprocess.check_call, [command], shell=True, job_id=name, 
            depends_on=depends_on, meta=meta, timeout=timeout, result_ttl=timeout
        )