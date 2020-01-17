# Did you source set_environment_local.sh prior to running
# this script? If not, it will fail.
import os


#: This folder is where all of your data lives for training and
#: evaluating. This folder will be mapped to /storage/data/ in your
#: docker container, allowing you to write the scripts in reference
#: to those locations. Make sure you have read/write permissions for 
#: the folder you are pointing to.
dataset_directory = os.getenv('DATA_DIRECTORY') 

#: This tells the Docker container where the code containing all of
#: your scripts are. When the container starts, this is the folder you
#: will be in. You can assume relative paths from the root of this code
#: directory in your script. It now just uses the current working directory.
code_directory = os.getenv('CODE_DIRECTORY')

#: The training scripts generate a cache of input/output pairs
#: for the network. These caches are zarr files that contain
#: all the input/output for the network and can be substantial
#: in size. It's good to know where they are so you can free up
#: hard drive space from time to time as needed.
cache_directory = os.getenv('CACHE_DIRECTORY')

#: The experiment scripts all output their results in custom
#: named folders whose names are randomly generated (by comet.ml).
#: These folders get saved to mapped to the same location inside the 
#: docker container. Good to know where these are so that you 
#: know where your results are.
artifacts_directory = os.getenv('ARTIFACTS_DIRECTORY')

#: This tells the Docker container where nussl is, so the scripts
#: can import your version of nussl. This is useful if
#: are editing nussl continuously and testing it. This is optional
#: as you could just use the version of nussl on Github. But if 
#: you're editing core nussl features, this is useful.
nussl_directory = os.getenv('NUSSL_DIRECTORY', artifacts_directory)

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

#: Arguments given by default when running a script.
default_script_args = {
    'run_in': 'host',
    'num_gpus': 0,
    'num_workers': 1,
    'blocking': False
}

if __name__ == '__main__':
    print(volumes)
