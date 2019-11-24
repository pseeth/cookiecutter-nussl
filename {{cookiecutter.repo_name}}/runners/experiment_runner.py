from comet_ml import BaseExperiment
BaseExperiment._report_summary = lambda args : None

from comet_ml import Experiment, ExistingExperiment
import logging
import docker
from .docker_runner import DockerRunner
import os, glob, json
from .config import artifacts_directory as global_artifacts_directory
import collections
import numpy as np
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread import WorksheetNotFound
from .utils import flatten, deep_update
import copy
import subprocess
import pickle
import yaml

class ExperimentRunner(object):
    def __init__(
        self, 
        api_key=None,
        parameters=None, 
        experiment_key=None, 
        artifacts_directory=None,
        credentials_path=None,
    ):
        artifacts_directory = (
            artifacts_directory 
            if artifacts_directory
            else os.getenv('ARTIFACTS_DIRECTORY')
        )

        api_key = api_key if api_key else os.getenv('COMET_API_KEY')

        self.credentials_path = {
            credentials_path if credentials_path 
            else os.getenv('PATH_TO_GOOGLE_CREDENTIALS')
        }

        parameters = parameters if parameters else {}
        
        if not parameters and not experiment_key:
            raise ValueError('Either parameters or experiment_key must be provided!')
        
        if experiment_key is not None:
            logging.info(f"Updating existing experiment: {experiment_key}")
            experiment = ExistingExperiment(
                api_key=api_key,
                previous_experiment=experiment_key
            )
            current_parameters = self.load_experiment_parameters(
                experiment_key, artifacts_directory)
            parameters = deep_update(current_parameters, parameters)
        else:
            experiment = Experiment(
                api_key=api_key,
                project_name=parameters['info']['project_name']
            )
        
        self.experiment_key = experiment.get_key()
        self.experiment_url = experiment._get_experiment_url()
        self.experiment = experiment
        if 'filename' in parameters:
            if os.path.exists(parameters['filename']):
                with open(parameters['filename'], 'r') as f:
                    data = f.read()
                self.experiment.set_code(data)
        self.runner = DockerRunner()
        self.parameters = parameters

        flattened_parameters = flatten(parameters)
        self.experiment.log_parameters(flattened_parameters)

        self.output_folder = os.path.join(artifacts_directory, self.experiment_key)
        os.makedirs(os.path.join(self.output_folder), exist_ok=True)

        fpath = os.path.join(self.output_folder, 'config.yml')
        with open(fpath, 'w') as f:
            yaml.safe_dump(parameters, f)
                
        self.init_gsheet(self.credentials_path)
        logging.info(
            f"Set up {self.experiment_key} - {self.parameters['info']['notes']}"
        )
        self.experiment.end()

    @staticmethod
    def load_experiment_parameters(experiment_key, artifacts_directory):
        current_parameters = {}
        config = os.path.join(artifacts_directory, experiment_key, 'config.yml')
        with open(config, 'r') as f:
            current_parameters = yaml.safe_load(f)
        return current_parameters

    def train(self):
        parameters = copy.deepcopy(self.parameters)
        train = parameters['info'].pop('train', False)
        if 'train_config' not in parameters:
            logging.info('No train_config available. Skipping training...')
            return
        if not train:
            logging.info("parameters['info']['train] is False. Skipping training...")
            return
        
        cache_populated = parameters['info'].pop('cache_populated', False)
        gpus = parameters['info'].pop('gpus', '')
        resume = parameters['info'].pop('resume', False)

        # make sure to have trailing spaces on each line
        command = (
            f"python train.py " 
            f"-e {self.experiment_key} " 
            f"{'-c' if cache_populated else ''} "
            f"{'-r' if resume else ''} "
        )
        return self.runner.run(command, gpus=gpus, name=f'exp.tr.{self.experiment_key}')

    def evaluate(self):
        parameters = copy.deepcopy(self.parameters)
        test = parameters['info'].pop('test', False)
        if not test:
            logging.info("parameters['info']['test] is False. Skipping training...")
            return
        test_folder = parameters['info'].pop('test_folder', '')
        test_dataset_type = parameters['info'].pop('test_dataset_type', '')
        num_test_workers = parameters['info'].pop('num_test_workers', 10)
        tag = parameters['info'].pop('tag', '')
        gpus = parameters['info'].pop('gpus', '')

        # make sure to have trailing spaces on each line
        command = (
            f"python test.py "
            f"-e {self.experiment_key}"
            f"{' -tf ' + test_folder if test_folder else ''}"
            f"{' -td ' + test_dataset_type if test_dataset_type else ''}"
            f"{' -t ' + tag if tag else ''}" 
            f" -n {num_test_workers}"
        )
    
        return self.runner.run(command, gpus=gpus, name=f'exp.tt.{self.experiment_key}')

    def wait(self):
        if self.runner.container:
            logging.info(
                f"\n\tWaiting. See progress @ {self.experiment_url}"
                f"\n\tOr run 'docker logs -f {self.experiment_key}' "
                f"\n\tNotes for this experiment: {self.parameters['info']['notes']}'"
            )
            try:
                self.runner.container.wait()
            except:
                pass

    def run(self):
        name = self.train()
        self.wait()
        
        name = self.evaluate()
        self.wait()

    def analyze(self, get_confidence=False, threshold=99):
        results_path = os.path.join(self.output_folder, 'results')
        json_files = sorted(glob.glob(os.path.join(results_path, '*/*.json')))
        results = []
        for json_file in json_files:
            with open(json_file, 'r') as f:
                data = json.load(f)
            if os.path.exists(json_file + '.pkl') and get_confidence:
                try:
                    with open(json_file + '.pkl', 'rb') as f:
                        extra_data = pickle.load(f)
                except:
                    extra_data = None
            else:
                extra_data = None
            source_names = sorted(list(data.keys()))
            source_names.remove('permutation')
            for source_name in source_names:
                flattened = {
                    'experiment_key': self.experiment_key,
                    'notes': self.parameters['info']['notes'],
                    'file_name': json_file.split('/')[-1],
                    'dataset': json_file.split('/')[-2],
                    'source_name': source_name,
                    'SDR': np.mean(data[source_name]['SDR']),
                    'SIR': np.mean(data[source_name]['SIR']),
                    'SAR': np.mean(data[source_name]['SAR']),
                }
                if extra_data:
                    for k in extra_data:
                        flattened[k] = extra_data[k]
                results.append(flattened)
        all_results = pd.DataFrame(results)
        self.results = all_results
        return all_results

    def init_gsheet(self, credentials_path):
        if credentials_path:
            scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
            self.gc = gspread.authorize(credentials)
        else:
            self.gc = None

    def upload_to_gsheet(self):
        if self.results is None:
            logging.info('Run analysis - self.analyze() - first before uploading!')
            return
        if not self.gc:
            logging.info('Credentials not provided for Google Sheets!')
            return

        self.init_gsheet(self.credentials_path)

        all_results = self.results
        parameters = copy.deepcopy(self.parameters)
        sheet_name = parameters['info'].pop('sheet_name', 'Experimental results')
        worksheet_name = parameters['info'].pop('worksheet_name', 'Summary')
        sheet = self.gc.open(sheet_name)

        try:
            summary_worksheet = sheet.worksheet(worksheet_name)
        except WorksheetNotFound:
            logging.info(f'Worksheet not found, creating new sheet w/ name {worksheet_name}')
            template_worksheet = sheet.worksheet('Template')
            summary_worksheet = template_worksheet.duplicate(new_sheet_name=worksheet_name)

        datasets = np.unique(all_results['dataset'])
        metrics = ['SDR', 'SIR', 'SAR']
        notes = parameters['info'].pop('notes', 'No notes')

        def trunc(values, decs=0):
            return np.trunc(values*10**decs)/(10**decs)

        existing_rows = summary_worksheet.get_all_values()

        for dataset in datasets:
            logging.info(
                f'Uploading results for {dataset} for {self.experiment_key} '
                f'@ {worksheet_name} in {summary_worksheet}'
            )
            results = all_results[all_results['dataset'] == dataset]
            dataset_paths = self.parameters['dataset_paths'].copy()
            row_to_insert = [
                f'=HYPERLINK("{self.experiment_url}", "{self.experiment_key}")',
                notes, 
                dataset_paths.pop('train_folder', 'No training'),
                dataset_paths.pop('val_folder', 'No validation.'),
                dataset,
                np.unique(results['file_name']).shape[0],
            ]

            row_exists = False
            row_index = 3
            for j, row in enumerate(existing_rows):
                compared_indices = [2, 3, 4]
                row = [row[0]] + [row[i] for i in compared_indices]
                inserted_row = [self.experiment_key] + [str(row_to_insert[i]) for i in compared_indices] 
                if (row == inserted_row):
                    logging.info("Row already exists")
                    row_exists = True
                    row_index = j + 1
                    break
            
            if not row_exists:
                summary_worksheet.insert_row(row_to_insert, index=3, value_input_option='USER_ENTERED')
            
            overall_metrics = [np.unique(results['file_name']).shape[0]] + [trunc(x, decs=2) for x in results.mean()[metrics]]
            overall_index = summary_worksheet.find('Overall').col - 1
            for i, value in enumerate(overall_metrics):
                summary_worksheet.update_cell(row_index, overall_index + i, value)

            source_names = np.unique(results['source_name']).tolist()
            for source_name in source_names:
                source_metrics = []
                try:
                    source_name_cell = summary_worksheet.find(source_name)
                except Exception as e:
                    source_name_cell = summary_worksheet.find('Source')
                    source_name_cell.value = source_name
                    summary_worksheet.update_cells([source_name_cell])
                for i, metric in enumerate(metrics):
                    value = trunc(
                        results[results['source_name'] == source_name].mean()[metric], decs=2)
                    summary_worksheet.update_cell(row_index, source_name_cell.col + i, value)