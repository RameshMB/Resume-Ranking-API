from __future__ import unicode_literals, print_function
import os
import json
import logging
from pathlib import Path
import spacy
from tqdm import tqdm  # loading bar

from settings import NLP_MODEL_Path, train_JSON_FilePath


def get_train_data():
    train_data, evaluate_data = [], []
    labels = set()
    train_label_values = {}
    folder_path = os.path.join(train_JSON_FilePath, 'valid_json')
    for file_count, json_fl in enumerate(os.listdir(folder_path)):
        json_file_path = os.path.join(folder_path, json_fl)
        with open(json_file_path, 'r', encoding='utf-8') as data_file:
            try:
                data = json.loads(data_file.read())
                filtered_data_entities = []
                for lbl in data['entities']:
                    if lbl[2] in ['Tools', 'Operating_Systems', 'Certifications', 'Tools.']:
                        continue
                    train_label_values[lbl[2]] = train_label_values.get(lbl[2], set())
                    train_label_values[lbl[2]].add(lbl[-1])
                    labels.add(lbl[2])
                    filtered_data_entities.append(lbl)
                spacy_format_data = tuple([data['text'], {'entities': [(ent[0], ent[1], ent[2]) for ent in filtered_data_entities]}])
                train_data.append(spacy_format_data)
            except Exception:
                import sys, linecache
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                linecache.checkcache(filename)
                line = linecache.getline(filename, lineno, f.f_globals)
                print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))
    for k, v in train_label_values.items():
        print(k, v)
    return labels, train_data


class TrainModel:

    def __init__(self, model=None):
        # Load The Models
        self.model = model
        if self.model is not None:
            model_path = os.path.join(NLP_MODEL_Path, self.model)
            if os.path.exists(model_path):
                self.nlp = spacy.load(model_path)  # load existing spaCy model
                logging.info('Loaded model "{0}" from path "{1}"'.format(self.model, model_path))
            else:
                logging.error(msg='Invalid model name "{0}"'.format(self.model))
                raise Exception('Model "{0}" does not exist.'.format(self.model))
        else:
            # self.nlp = spacy.load('en_core_web_sm')  # create blank Language class
            self.nlp = spacy.blank('en')  # create blank Language class
            logging.info('Created blank model')

    def train(self, train_data, n_iter=50):
        logging.info('Training model "{0}"'.format(self.model))
        # Add entity recognizer to model if it's not in the pipeline
        # nlp.create_pipe works for built-ins that are registered with spaCy
        if 'ner' not in self.nlp.pipe_names:
            ner = self.nlp.create_pipe('ner')
            self.nlp.add_pipe(ner)
        # otherwise, get it, so we can add labels to it
        else:
            ner = self.nlp.get_pipe('ner')

        # add labels
        for _, annotations in train_data:
            for ent in annotations.get("entities"):
                ner.add_label(ent[2])

        if self.model is None:
            optimizer = self.nlp.begin_training()
        else:
            optimizer = self.nlp.entity.create_optimizer()

        for itn in range(n_iter):
            print('\nIteration {}/{}'.format(itn+1, n_iter))
            logging.info('\nIteration {}/{}'.format(itn+1, n_iter))
            # random.shuffle(train_data)
            losses = {}
            for text, annotations in tqdm(train_data):
                self.nlp.update([text], [annotations], sgd=optimizer, drop=0.35, losses=losses)
            logging.debug(losses)

    def get_entities(self, text):
        entity = {}
        logging.info('Get Entities from text: "{0}"'.format(text))
        try:
            doc = self.nlp(text)
            for ent in doc.ents:
                entity[ent.label_] = entity.get(ent.label_, [])
                if ent.text not in entity[ent.label_]:
                    entity[ent.label_].append(ent.text)
            if 'Years_of_Experience' in entity and entity['Years_of_Experience']:
                for word in entity['Years_of_Experience'][0].split():
                    if '+' in word:
                        word = word.split('+', 1)[0]
                    try:
                        entity['Years_of_Experience'] = float(word)
                    except ValueError:
                        pass
            logging.debug(entity)
        except Exception as err:
            logging.exception('Unable to get entities Error:{0}'.format(str(err)))
        for lbl in self.trained_labels():
            entity[lbl] = entity.get(lbl, [])
        if entity["Name"]:
            entity["Name"] = entity["Name"][0]
        return json.dumps(entity)

    def save_model(self, model):
        model_path = os.path.join(NLP_MODEL_Path, model)
        output_dir = Path(model_path)
        if not output_dir.exists():
            output_dir.mkdir()
        self.nlp.meta['name'] = model  # rename model
        self.nlp.to_disk(model_path)
        logging.info('Saved "{0}" model to "{1}"'.format(model, output_dir))

    def trained_labels(self):
        return self.nlp.entity.labels


def train_model():
    labels, train_data = get_train_data()
    ner_obj = TrainModel()
    ner_obj.train(train_data=train_data, n_iter=100)
    ner_obj.save_model(model='Resume_Keyword_Extraction')


if __name__ == '__main__':
    # train_model()
    ner_obj = TrainModel(model='Resume_Keyword_Extraction')
    print(ner_obj.get_entities(text=open('../test.txt', 'r', encoding='utf-8').read()))
    print(ner_obj.trained_labels())
