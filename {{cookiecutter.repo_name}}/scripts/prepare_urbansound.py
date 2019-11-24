import sys
sys.path.insert(0, '.')

import csv
import os
import shutil
from cookiecutter_repo.utils.parallel import parallel_process
from multiprocessing import cpu_count

data_directory = os.path.join(os.getenv('DATA_DIRECTORY'), 'urbansound8k')
train_folds = [1, 2, 3, 4, 5, 6, 7, 8]
val_folds = [9]
test_folds = [10]

for d in ['train', 'validation', 'test']:
    os.makedirs(
        os.path.join(data_directory, 'data', d),
        exist_ok=True)

def copy_audio_to_folder_of_class(row):
    target_directory = data_directory
    class_name = row['class']
    source_file = os.path.join(data_directory, 'audio', f"fold{row['fold']}", row['slice_file_name'])
    if int(row['fold']) in train_folds:
        target_directory = os.path.join(target_directory, 'train', class_name)
    elif int(row['fold']) in val_folds:
        target_directory = os.path.join(target_directory, 'validation', class_name)
    else:
        target_directory = os.path.join(target_directory, 'test', class_name)

    os.makedirs(target_directory, exist_ok=True)
    target_file = os.path.join(target_directory, row['slice_file_name'])

    print(f"Copying {source_file} w/ fold {row['fold']} to {target_file}", flush=True)
    shutil.copyfile(source_file, target_file)


with open(os.path.join(data_directory, 'metadata', 'UrbanSound8K.csv'), 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

parallel_process(rows, copy_audio_to_folder_of_class, n_jobs=cpu_count(), front_num=1)