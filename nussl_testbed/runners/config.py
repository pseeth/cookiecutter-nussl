# Did you source set_environment_local.sh prior to running
# this script? If not, it will fail.
import os

dataset_directory = os.getenv('DATA_DIRECTORY')
code_directory = os.getenv('CODE_DIRECTORY')
cache_directory = os.getenv('CACHE_DIRECTORY')
artifacts_directory = os.getenv('ARTIFACTS_DIRECTORY')
nussl_directory = os.getenv('NUSSL_DIRECTORY')

volumes = {
    nussl_directory: {
        'bind': nussl_directory,
        'mode': 'rw'
    },
    dataset_directory: {
        'bind': dataset_directory,
        'mode': 'rw'
    },
    code_directory: {
        'bind': '/workspace',
        'mode': 'rw'
    },
    cache_directory: {
        'bind': cache_directory,
        'mode': 'rw'
    },
    artifacts_directory: {
        'bind': artifacts_directory,
        'mode':  'rw'
    },
}

default_script_args = {
    'run_in': 'host',
    'num_gpus': 0,
    'num_workers': 1,
    'blocking': False
}

if __name__ == '__main__':
    print(volumes)
