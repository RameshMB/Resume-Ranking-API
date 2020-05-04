import json
import logging
import os
import shutil
from settings import train_JSON_FilePath


logging.info('Validating json files......')
no_of_files_found = os.listdir(train_JSON_FilePath)
if not no_of_files_found:
    logging.info('.json files not found.....')
else:
    for json_file in no_of_files_found:
        json_file_path = os.path.join(train_JSON_FilePath, json_file)
        valid_json_file_path = os.path.join(train_JSON_FilePath, 'valid_json', json_file)
        logging.info('Processing {}'.format(json_file_path))
        if json_file_path.endswith('.json'):
            data_error = False
            error_in = ''
            with open(json_file_path) as f:
                data = json.load(f)
                for ent in data['entities']:
                    if data['text'][ent[0]:ent[1]] != ent[3]:
                        data_error = True
                        error_in = "Text {} != label {}".format(data['text'][ent[0]:ent[1]], ent[3])
                        break
            if data_error:
                logging.info('Invalid json file {}'.format(json_file_path))
            else:
                shutil.move(json_file_path, valid_json_file_path)
                logging.info('Completed json file validation....')
                logging.info('Moved {} to valid_json folder'.format(json_file_path))
        logging.info('All file validation process is completed.')
