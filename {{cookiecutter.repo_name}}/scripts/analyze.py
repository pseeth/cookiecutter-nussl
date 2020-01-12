import sys
sys.path.insert(0, '.')

from runners.experiment_utils import load_experiment, save_experiment
from cookiecutter_repo import logging
from runners.utils import build_parser_for_yml_script, load_yaml, flatten
import glob
import pandas as pd
import os
import copy
import numpy as np

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread import WorksheetNotFound

def init_gsheet(credentials_path):
    scope = ['https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        credentials_path, scope
    )
    gc = gspread.authorize(credentials)
    return gc

def upload_to_gsheet(results, config, exp):
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
    logging.info(config['info'])
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
        logging.info(_results)
        overall_metrics = (
            [np.unique(_results['file_name']).shape[0]] + 
            [trunc(x, decs=2) for x in _results.mean()[metrics]]
        )
        overall_index = summary_worksheet.find('Overall').col - 1
        for i, value in enumerate(overall_metrics):
            summary_worksheet.update_cell(row_index, overall_index + i, value)

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

def main(path_to_yml_file):
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
    return results, config, exp

if __name__ == '__main__':
    parser = build_parser_for_yml_script()
    args = vars(parser.parse_args())
    results, config, exp = main(args['spec'])
    keys = [k for k in results.keys() if k not in ['dataset', 'notes', 'source_name']]
    logging.info(results[keys].to_string())

    upload_to_gsheet(results, config, exp)
    