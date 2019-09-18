import os
import pymongo
import os.path
from extract_text_from_files import extract_text_from_pdf_file, get_text_from_docx_file, get_text_from_text_file
from ner_model_train import TrainModel
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# path = r'C:\\Users\\Vidagotti.Raju\\PycharmProjects\\Code_Practice\\upload_files\\damu\\Java'
# path = r".\upload_files\damu\Java"
# path = r'C:\Users\Vidagotti.Raju\Desktop\Resume AIML'
# path = r"C:\Users\Vidagotti.Raju\PycharmProjects\Code_Practice\upload_files\damu\Java"
# def get_catalogue_files(path):
#     # check directory exists
#     if (os.path.exists(path)):
#         #check file exists
#         if (os.path.exists(path)):
#             print('path',path)
#             for file_name in os.listdir(path):
#                 print('file_name:',file_name)
#                 file_type = file_name.rsplit('.', 1)[1].lower()
#                 print('file_type:',file_type)
#                 file_data = ''
#                 file_path = os.path.join(path,file_name)
#                 if file_type == "txt":
#                     file_data = get_text_from_text_file(file_path)
#                     print(file_data)
#                 elif file_type == "pdf":
#                     file_data = extract_text_from_pdf_file(file_path)
#                     print(file_data)
#                 elif file_type == "docx":
#                     file_data = get_text_from_docx_file(file_path)
#                     print(file_data)
#                 # nlp_obj = TrainModel(model='Resume_Keyword_Extraction')
#                 # entity_data = nlp_obj.get_entities(text=file_data)
#                 # return json.dumps(entity_data)
#                 # return file_data

# get_catalogue_files(path)

def get_catalogue():
    client = pymongo.MongoClient('localhost:27017')
    db = client['Resume_Ranking']
    catalog_resume_col = db['catalog_resumes']
    users_catalog_col = db['user_catalog']
    # resume_files = catalog_resume_col.find({},{'catalog_id':1,'is_entity_extracted':1})
    resume_files = list(catalog_resume_col.find())
    # print('resume_files:',resume_files)
    catlog_col = list(users_catalog_col.find())
    # print('catlog_col',catlog_col)
    nlp_obj = TrainModel(model='Resume_Keyword_Extraction')
    for file in resume_files:
        print('file',file)
        if file['catalog_id'] == catlog_col[0]['_id'] and file['is_entity_extracted'] == False:
            file_name=file['file_name']
            # print('file_name',file_name)
            file_path = file['file_path']
            file_path = os.path.join(APP_ROOT, file_path, file_name)
            # print('file_path',file_path)
            file_type = file_name.rsplit('.',1)[1].lower()
            # print('file_type',file_type)
            if file_type == "txt":
                file_data = get_text_from_text_file(file_path)
            elif file_type == "pdf":
                file_data = extract_text_from_pdf_file(file_path)
            elif file_type == "docx":
                file_data = get_text_from_docx_file(file_path)
            # print('file_data',file_data)
            entity_data = nlp_obj.get_entities(text=file_data)

get_catalogue()