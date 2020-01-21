import os
import glob

directory = os.path.join(os.getenv('DATA_DIRECTORY'), 'speech_commands/all')
all_files = glob.glob(
    f'{directory}/*/**.wav', 
    recursive=True
)
all_files = [x.replace(directory, '')[1:] for x in all_files]

with open(f'{directory}/testing_list.txt') as f:
    test_files = f.readlines()
    test_files = [x.strip() for x in test_files]

with open(f'{directory}/validation_list.txt') as f:
    val_files = f.readlines()
    val_files = [x.strip() for x in val_files]

tr_files = list(set(all_files) - set(test_files + val_files))
assert(len(all_files) == (len(tr_files) + len(val_files) + len(test_files)))

with open(f'{directory}/training_list.txt', 'w') as f:
    for x in tr_files:
        f.write(x+'\n')