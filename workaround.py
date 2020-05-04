import os
import json

from settings import CATALOG_FILES_COL, UPLOAD_FILE_PATH
from ner_model.ner_model_train import TrainModel
from files.extract_text_from_files import get_text_from_docx_file, get_text_from_text_file, extract_text_from_pdf_file


def remove_columns_from_files_docs():
    for file in CATALOG_FILES_COL.find():
        print(file)
        CATALOG_FILES_COL.update({"_id": file["_id"]}, {"$unset": {
            "College_Name": 1,
            "Companies_worked_at": 1,
            "Designation": 1,
            "Tools": 1
        }})


def process_all_files():
    catalog_resumes = CATALOG_FILES_COL.find()
    nlp_obj = TrainModel(model='Resume_Keyword_Extraction')
    for file_doc in catalog_resumes:
        file_full_path = os.path.join(UPLOAD_FILE_PATH, str(file_doc["catalog"]), file_doc["file_name"])
        file_type = file_doc['file_name'].rsplit('.', 1)[1].lower()
        if file_type == "txt":
            file_data = get_text_from_text_file(file_full_path)
        elif file_type == "pdf":
            file_data = extract_text_from_pdf_file(file_full_path)
        elif file_type == "docx":
            file_data = get_text_from_docx_file(file_full_path)
        entity_data = nlp_obj.get_entities(text=file_data)
        entity_data = json.loads(entity_data)
        entity_data['is_entity_extracted'] = True
        CATALOG_FILES_COL.update({"_id": file_doc['_id']}, {"$set": entity_data})


if __name__ == '__main__':
    process_all_files()
