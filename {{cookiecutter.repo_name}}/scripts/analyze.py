from runners.experiment_utils import load_experiment, save_experiment
from src import logging
from runners.utils import load_yaml, flatten
from . import cmd, document_parser
import glob
import pandas as pd
import os
import copy
import numpy as np
from argparse import ArgumentParser

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread import WorksheetNotFound

def init_gsheet(credentials_path):
    """
    Initializes the Google Sheets client given a path to credentials.
    
    Args:
        credentials_path (str): path to your Google credentials that are used to
            authorize the Google Sheets access.
    
    Returns:
        :class:`gspread.Client`: Google Sheets Client initialized with credentials.
    """
    scope = ['https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        credentials_path, scope
    )
    gc = gspread.authorize(credentials)
    return gc

def upload_to_gsheet(results, config, exp=None, upload_source_metrics=False):
    """
    Uploads the analysis to the Google Sheet, if possible.
    
    Args:
        results (:class:`pandas.DataFrame`): DataFrame containing all the results - output
            by :py:func:`scripts.analyze.analyze`.
        config (dict): Dictionary containing the entire experiment configuration.
        exp (:class:`comet_ml.Experiment`): Experiment given by comet.ml (optional).
        upload_source_metrics (bool): Uploads metrics for each source if True. Defaults to False.
            Can have interactions with the API limit on Google Sheets. If there are two many 
            sources, then it will hit the limit and the script will break.
    """
    credentials_path = os.getenv('PATH_TO_GOOGLE_CREDENTIALS', None)
    if not credentials_path:
        logging.info('PATH_TO_GOOGLE_CREDENTIALS not set, cannot proceed.')
        return None

    gc = init_gsheet(credentials_path)

    config = copy.deepcopy(config)
    sheet_name = config['info'].pop('spreadsheet_name', None)
    worksheet_name = config['info'].pop('worksheet_name', None)
    if not sheet_name or not worksheet_name:
        logging.info('Sheet name not specified, not uploading results to Google sheets')
        return None
    logging.info(f'Opening {sheet_name} with {worksheet_name}')
    sheet = gc.open(sheet_name)

    try:
        summary_worksheet = sheet.worksheet(worksheet_name)
    except WorksheetNotFound:
        logging.info(f'Worksheet not found, creating new sheet w/ name {worksheet_name}')
        template_worksheet = sheet.worksheet('Template')
        summary_worksheet = template_worksheet.duplicate(new_sheet_name=worksheet_name)

    datasets = np.unique(results['dataset'])
    metrics = ['SDR', 'SIR', 'SAR']
    notes = config['info'].pop('notes', 'No notes')

    def trunc(values, decs=0):
        return np.trunc(values*10**decs)/(10**decs)

    existing_rows = summary_worksheet.get_all_values()

    for dataset in datasets:
        logging.info(
            f"Uploading results for {dataset} for {config['info']['experiment_key']} "
            f"@ {worksheet_name} in {summary_worksheet}"
        )
        _results = results[results['dataset'] == dataset]
        dataset_paths = {
            key: config['datasets'][key]['folder'] 
            for key in config['datasets']
        }
        experiment_key = config['info']['experiment_key']
        experiment_url = 'No link'
        if hasattr(exp, '_get_experiment_url'):
            experiment_url = exp._get_experiment_url()
        row_to_insert = [
            f'=HYPERLINK("{experiment_url}", "{experiment_key}")',
            notes, 
            dataset_paths.pop('train', 'No training'),
            dataset_paths.pop('val', 'No validation.'),
            dataset,
            np.unique(_results['file_name']).shape[0],
        ]

        row_exists = False
        row_index = 3
        for j, row in enumerate(existing_rows):
            compared_indices = [2, 3, 4]
            row = [row[0]] + [row[i] for i in compared_indices]
            inserted_row = (
                [config['info']['experiment_key']] + 
                [str(row_to_insert[i]) for i in compared_indices] 
            )
            if (row == inserted_row):
                logging.info("Row already exists")
                row_exists = True
                row_index = j + 1
                break
        
        if not row_exists:
            summary_worksheet.insert_row(
                row_to_insert, index=3, value_input_option='USER_ENTERED'
            )
        overall_metrics = (
            [np.unique(_results['file_name']).shape[0]] + 
            [trunc(x, decs=2) for x in _results.mean()[metrics]]
        )
        overall_index = summary_worksheet.find('Overall').col - 1
        for i, value in enumerate(overall_metrics):
            summary_worksheet.update_cell(row_index, overall_index + i, value)

        if upload_sources:
            try:
                source_names = np.unique(_results['source_name']).tolist()
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
                            _results[_results['source_name'] == source_name].mean()[metric], 
                            decs=2
                        )
                        summary_worksheet.update_cell(
                            row_index, source_name_cell.col + i, value
                        )
            except:
                logging.info("Failure in uploading. Likely too many unique sources and we hit an API limit.")
                pass

def analyze(path_to_yml_file, use_gsheet=False, upload_source_metrics=False):
    """
    Analyzes the metrics for all the files that were evaluated in the experiment.
    
    Args:
        path_to_yml_file (str): Path to the yml file that defines the experiment. The
            corresponding results folder for the experiment is what will be analyzed and put
            into a Pandas dataframe.
        use_gsheet (bool, optional): Whether or not to upload to the Google Sheet. 
            Defaults to False.
        upload_source_metrics (bool): Uploads metrics for each source if True. Defaults to False.
            Can have interactions with the API limit on Google Sheets. If there are two many 
            sources, then it will hit the limit and the script will break.
    
    Returns:
        tuple: 3-element tuple containing

            - results (:class:`pandas.DataFrame`): DataFrame containing all of the results 
              for every file evaluated in the experiment. The DataFrame also has every
              key in the experiment configuration in flattened format.
              
              For example, model_config_recurrent_stack_args_embedding_size is a column in the DataFrame.

            - config (*dict*):  A dictionary containing the configuration of the experiment. 

            - exp (:class:`comet_ml.Experiment`): An instantiated experiment if comet.ml is needed,  otherwise it is None.
    """
    config, exp, path_to_yml_file = load_experiment(path_to_yml_file)
    
    paths = glob.glob(
        os.path.join(config['info']['output_folder'], 'results', '**.yml'),
        recursive=True
    )

    results = []

    for _path in paths:
        data = load_yaml(_path, [])
        for _data in data:
            keys = sorted(list(_data.keys()))
            keys.remove('permutation')
            for key in keys:
                flattened = {
                    'experiment_key': config['info']['experiment_key'],
                    'notes': config['info']['notes'],
                    'file_name': _path,
                    'dataset': config['datasets']['test']['folder'],
                    'source_name': key.split('/')[-1],
                }

                flattened.update(flatten(config))

                for metric in _data[key]:
                    flattened[metric] = np.mean(_data[key][metric])

                results.append(flattened)
    
    results = pd.DataFrame(results)

    logging.info(results.mean())
    logging.info(config['info']['experiment_key'])

    if use_gsheet:
        upload_to_gsheet(results, config, exp, upload_source_metrics)

    return results, config, exp

@document_parser('analyze', 'scripts.analyze.analyze')
def build_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "-p",
        "--path_to_yml_file",
        type=str,
        required=True,
        help="""Path to the configuration for the experiment that is getting analyzed. The
        corresponding results folder for the experiment is what will be analyzed and put
        into a Pandas dataframe.
        """
    )
    parser.add_argument(
        "--use_gsheet",
        action="store_true",
        help="""Results can be synced to a Google sheet after analysis if this is true.
        Defaults to false.
        """
    )
    parser.add_argument(
        "--upload_source_metrics",
        action="store_true",
        help="""Uploads metrics for each source if True. Defaults to False.
        Can have interactions with the API limit on Google Sheets. If there are two many 
        sources, then it will hit the limit and the script will break.
        """
    )
    return parser

if __name__ == '__main__':
    cmd(analyze, build_parser) 