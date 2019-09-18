import os
import pymongo

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # This is Project Root
train_JSON_FilePath = os.path.join(ROOT_DIR, r'data/train')
data_turks_JSON_FilePath = os.path.join(ROOT_DIR, r'data/data_turks_json')
NLP_MODEL_Path = os.path.join(ROOT_DIR, r'nlp_models')
UPLOAD_FILE_PATH = os.path.join(ROOT_DIR, r'upload_files')
upload_files = os.path.join(ROOT_DIR, 'upload_files')

client = pymongo.MongoClient("mongodb://localhost:27017/")

MONGO_DB = client.get_database("ResumeRankingDB")
CATALOG_FILES_COL = MONGO_DB["catalog_files"]
USER_CATALOGS_COL = MONGO_DB["user_catalogs"]
USERS_COL = MONGO_DB["users"]
