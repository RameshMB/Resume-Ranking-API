import json
import logging
from datetime import timezone, datetime
import os
import shutil
from settings import data_turks_JSON_FilePath, train_JSON_FilePath


logging.info('Dataturks json conversion to spacy started......')
no_of_files_found = os.listdir(data_turks_JSON_FilePath)
if not no_of_files_found:
    logging.info('.json files not found.....')
else:
    for json_file in no_of_files_found:
        json_file_path = os.path.join(data_turks_JSON_FilePath, json_file)
        process_file_path = os.path.join(data_turks_JSON_FilePath, 'processed', json_file)
        logging.info('Processing {}'.format(json_file_path))
        if json_file_path.endswith('.json'):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    data = json.loads(line)
                    if not data['annotation']:
                        logging.exception("Not Annoated this data" + line)
                        continue
                    text = data['content']
                    entities = []
                    for annotation in data['annotation']:
                        # only a single point in text annotation.
                        point = annotation['points'][0]
                        labels = annotation['label']
                        # handle both list of labels or a single label.
                        if not isinstance(labels, list):
                            labels = [labels]

                        for label in labels:
                            entity = point['text']
                            leading_spaces = len(entity) - len(entity.lstrip())
                            trailing_spaces = len(entity) - len(entity.rstrip())
                            entity = entity.strip()
                            start = point['start']+leading_spaces
                            end = point['end'] + 1 - trailing_spaces
                            # dataturks indices are both inclusive [start, end] but spacy is not [start, end)
                            entities.append((start, end, label, entity))
                    unix_time = datetime.now(tz=timezone.utc).timestamp() * 1000
                    filename = str(unix_time) + '.json'
                    file_path = os.path.join(train_JSON_FilePath, filename)
                    with open(file_path, 'w') as json_f:
                        json.dump({'text': text, "entities": entities}, json_f)
                    logging.info('json created successfully for the resume....' + line)
            shutil.move(json_file_path, process_file_path)
            logging.info('Completed json conversion....')
            logging.info('Moved {} to processed folder'.format(json_file_path))
