import os
from bson import ObjectId

from datetime import datetime

from settings import ROOT_DIR, USERS_COL, USER_CATALOGS_COL, CATALOG_FILES_COL

ALLOWED_EXTENSIONS = ['txt', 'pdf', 'docx']
APP_ROOT = os.path.dirname(os.path.abspath(__file__))


def save_file(file, file_doc):
    full_path = os.path.join(ROOT_DIR, 'upload_files', str(file_doc["catalog"]))
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    file_full_path = os.path.join(full_path, file.filename)
    file.save(file_full_path)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_upload_files(uploaded_files):
    valid = True
    for file in uploaded_files:
        if not allowed_file(file.filename):
            valid = False
            break
    return valid


def validate_user(user_id):
    user = USERS_COL.find_one({'_id': user_id})
    if not user:
        return None
    return user


def validate_catalog(user, catalog_name, create=False):
    user_catalog = USER_CATALOGS_COL.find_one({
        'user': user['_id'],
        'name': catalog_name
    })
    if not user_catalog:
        if create is True:
            new_catalog = {
                "user": user['_id'],
                "name": catalog_name,
                "data_un_extracted_files": 0,
                "prev_data_extracted_date": None,
                "created_date": datetime.now()
            }
            user_catalog = USER_CATALOGS_COL.insert_one(new_catalog)
            new_catalog['_id'] = user_catalog.inserted_id
            user_catalog = new_catalog
            return user_catalog
        else:
            return False
    return user_catalog


def validate_catalog_file(catalog, file_name):
    catalog_resume_doc = CATALOG_FILES_COL.find_one({'catalog': catalog['_id'], 'file_name': file_name})
    if not catalog_resume_doc:
        new_catalog_resume_doc = {
            'catalog': catalog['_id'],
            'file_name': file_name,
            'is_active': True,
            'is_entity_extracted': True,
            'created_date': datetime.now()
        }
        catalog_resumes = CATALOG_FILES_COL.insert_one(new_catalog_resume_doc)
        new_catalog_resume_doc['_id'] = catalog_resumes.inserted_id
        catalog_resume_doc = new_catalog_resume_doc
    return catalog_resume_doc


def update_file(up_file_doc):
    CATALOG_FILES_COL.update_one({"_id": up_file_doc["_id"]}, {'$set': {'is_entity_extracted': False}})
    return up_file_doc


def shortlist_catalog_profiles(user_id, catalog_id, min_exp, max_exp, req_skills, qualification=None, opt_skills=None):
    points_per_req_skill = 10
    points_per_opt_skill = 5
    opt_skills_score = 0
    if not req_skills:
        raise Exception("'req_skills' should not be empty.")
    else:
        req_skills_score = len(req_skills) * points_per_req_skill
    if opt_skills:
        opt_skills_score = len(opt_skills) * points_per_opt_skill
    try:
        catalog_id = ObjectId(catalog_id)
        catalog_files = CATALOG_FILES_COL.find({"catalog": catalog_id, "is_active": True, "is_entity_extracted": True})
        matched_files = []
        for file in catalog_files:
            if "Years_of_Experience" not in file.keys():
                continue
            if isinstance(file["Years_of_Experience"], list):
                continue
            if min_exp and max_exp:
                if not min_exp <= float(file["Years_of_Experience"]) <= max_exp:
                    continue
            file['matched_req_skills'] = list(set(req_skills).intersection(set(file["Skills"])))
            if not file['matched_req_skills']:
                continue
            file['req_skill_match_score'] = len(file['matched_req_skills']) * points_per_req_skill
            if qualification is not None and "Degree" in file.keys():
                file['match_qualification'] = list(set(qualification).intersection(set(file["Degree"])))
            if opt_skills is not None:
                file['matched_opt_skills'] = list(set(opt_skills).intersection(set(file["Skills"])))
                file['opt_skill_match_score'] = len(file['matched_opt_skills']) * points_per_opt_skill
            file['Total_Match_Score'] = 0
            if req_skills and opt_skills:
                file['Total_Match_Score'] = ((file['req_skill_match_score'] + file['opt_skill_match_score'])/(
                        req_skills_score + opt_skills_score)) * 100.0
            elif req_skills and not opt_skills:
                file['Total_Match_Score'] = (file['req_skill_match_score'] / req_skills_score) * 100.0
            file['Total_Match_Score'] = round(file['Total_Match_Score'], 2)
            file['download_url'] = "http://localhost:5000/download-resume?user_id={}&catalog_id={}&file_id={}".format(
                str(user_id), str(file["catalog"]), str(file["_id"]))
            if 'created_date' in file.keys():
                file["created_date"] = file["created_date"].strftime("%d-%m-%Y")
            matched_files.append(file)
        matched_files = sorted(matched_files, key=lambda i: i['Total_Match_Score'], reverse=True)
        return matched_files
    except Exception as err:
        raise Exception(err)


if __name__ == '__main__':
    req_skill = ["JAVA", "Spring", "SQL", "JSP"]
    shortlist_catalog_profiles(catalog_id="5d78c795dcd2b1d84d491729", min_exp=2.0, max_exp=10.0,
                               req_skills=req_skill, qualification=['B.Tech.'], opt_skills=['Python'])
