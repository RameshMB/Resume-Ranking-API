import json
import os

from bson import ObjectId
from flask import Flask, request, send_file
from flask_cors import CORS

from common_functions import save_file, update_file, \
    validate_catalog_file, validate_upload_files, validate_user, validate_catalog, shortlist_catalog_profiles
from extract_text_from_files import extract_text_from_pdf_file, get_text_from_docx_file, get_text_from_text_file
from ner_model_train import TrainModel
from settings import UPLOAD_FILE_PATH, USER_CATALOGS_COL, USERS_COL, CATALOG_FILES_COL

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FILE_PATH
app.config['SECRET_KEY'] = 'kmykey'

CORS(app)


@app.route('/user-catalogs', methods=["POST"])
def get_user_catalogs():
    try:
        req_data = request.get_json()
        user_id = ObjectId(str(req_data['user_id']))
        user = validate_user(user_id)
        if user is None:
            response = {"status": "error", "message": "Invalid user_id '{}'".format(user_id)}
            return json.dumps(response)
        user_catalogs_docs = USER_CATALOGS_COL.find({"user": user_id})
        catalog_names = [ct["name"] for ct in user_catalogs_docs]
        response = {"status": "success", "data": catalog_names}
    except Exception as err:
        response = {"status": "error", "message": str(err)}
    return json.dumps(response)


@app.route('/upload-catalog-resumes', methods=['POST'])
def upload_catalog_files():
    try:
        user_id = ObjectId(str(request.form.get('user_id')))
        catalog_name = str(request.form.get('catalog_name')).strip()
        uploaded_files = request.files.getlist("file")
        if not validate_upload_files(uploaded_files):
            response = {"status": "error", "message": "Invalid file types. Please upload only .txt, .pdf, .docx files."}
            return json.dumps(response)
        user = validate_user(user_id)
        if user is None:
            response = {"status": "error", "message": "Invalid user_id '{}'".format(user_id)}
            return json.dumps(response)
        user_catalog = validate_catalog(user=user, catalog_name=catalog_name)
        for up_file in uploaded_files:
            up_file_doc = validate_catalog_file(catalog=user_catalog, file_name=up_file.filename)
            if up_file_doc['is_entity_extracted']:
                update_file(up_file_doc)
            save_file(file=up_file, file_doc=up_file_doc)
        return json.dumps({'status': 'success',
                           'message': '{} file(s) uploaded into "{}" catalog.'.format(len(uploaded_files), catalog_name)})
    except Exception as err:
        return json.dumps({'status': 'error', 'message': str(err)})


@app.route('/process-catalog-resumes', methods=['POST'])
def process_catalog_files():
    req_data = request.get_json()
    user_id = ObjectId(str(req_data['user_id']))
    catalog_name = str(req_data['catalog'])
    user = validate_user(user_id)
    if user is None:
        response = {"status": "error", "message": "Invalid user_id '{}'".format(user_id)}
        return json.dumps(response)

    user_cat_col = USER_CATALOGS_COL.find_one({"user": user["_id"], "name": catalog_name})
    catalog_resumes = CATALOG_FILES_COL.find({'catalog': user_cat_col['_id'], 'is_entity_extracted': False})
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
    return 'processed'


@app.route('/get-catalog-skills', methods=["POST"])
def get_catalog_skills():
    try:
        req_data = request.get_json()
        user_id = ObjectId(str(req_data['user_id']))
        catalog_name = str(req_data['catalog'])
        user = validate_user(user_id)
        if user is None:
            response = {"status": "error", "message": "Invalid user_id '{}'".format(user_id)}
            return json.dumps(response)
        user_cat_col = USER_CATALOGS_COL.find_one({'user': user["_id"], "name": catalog_name})
        catalog_resume = CATALOG_FILES_COL.find({'catalog': user_cat_col['_id']})
        skills = catalog_resume.distinct("Skills")
        skills.sort()
        response = {"status": "success", "skills": skills}
    except Exception as err:
        response = {
            "status": "error",
            "message": str(err)
        }
    return json.dumps(response)


@app.route('/get-catalog-qualification', methods=["POST"])
def get_catalog_degrees():
    try:
        req_data = request.get_json()
        user_id = ObjectId(str(req_data['user_id']))
        catalog_name = str(req_data['catalog'])
        user = validate_user(user_id)
        if user is None:
            response = {"status": "error", "message": "Invalid user_id '{}'".format(user_id)}
            return json.dumps(response)
        user_cat_col = USER_CATALOGS_COL.find_one({'user': user["_id"], "name": catalog_name})
        catalog_resume = CATALOG_FILES_COL.find({'catalog': user_cat_col['_id']})
        degree = catalog_resume.distinct("Degree")
        degree.sort()
        response = {"status": "success", "qualifications": degree}
    except Exception as err:
        response = {
            "status": "error",
            "message": str(err)
        }
    return json.dumps(response)


@app.route('/get-catalog-files', methods=["POST"])
def get_catalog_files():
    try:
        req_data = request.get_json()
        user_id = ObjectId(str(req_data['user_id']))
        catalog_name = str(req_data['catalog'])
        user = validate_user(user_id)
        if user is None:
            response = {"status": "error", "message": "Invalid user_id '{}'".format(user_id)}
            return json.dumps(response)
        user_cat_col = USER_CATALOGS_COL.find_one({'user': user["_id"], "name": catalog_name})
        catalog_resume = list(CATALOG_FILES_COL.find({'catalog': user_cat_col['_id']}))
        response = {"status": "success", "files": catalog_resume}
    except Exception as err:
        response = {
            "status": "error",
            "message": str(err)
        }
    return json.dumps(response, default=str)


@app.route('/short-list-profiles', methods=["POST"])
def profile_shortlist():
    try:
        req_data = request.get_json()
        user_id = ObjectId(str(req_data['user_id']))
        catalog_name = str(req_data['catalog'])
        min_experience = float(req_data['min_exp'])
        max_experience = float(req_data['max_exp'])
        required_skills = list(req_data['req_skills'])
        optional_skills = list(req_data['opt_skills'])
        qualifications = list(req_data['qualifications'])
        user = validate_user(user_id)
        if user is None:
            response = {"status": "error", "message": "Invalid user_id '{}'".format(user_id)}
            return json.dumps(response)
        user_cat_col = USER_CATALOGS_COL.find_one({'user': user["_id"], "name": catalog_name})
        matched_profiles = shortlist_catalog_profiles(user_id=user["_id"], catalog_id=user_cat_col["_id"],
                                                      min_exp=min_experience, max_exp=max_experience,
                                                      req_skills=required_skills, opt_skills=optional_skills,
                                                      qualification=qualifications)
        response = {"status": "success", "files": matched_profiles}
    except Exception as err:
        response = {
            "status": "error",
            "message": str(err)
        }
    return json.dumps(response, default=str)


@app.route('/download-resume', methods=["GET"])
def download_file():
    req_data = request.args
    user_id = ObjectId(str(req_data['user_id']))
    catalog_id = ObjectId(req_data['catalog_id'])
    file_id = ObjectId(req_data['file_id'])
    user = validate_user(user_id)
    if user is None:
        response = {"status": "error", "message": "Invalid user_id '{}'".format(user_id)}
        return json.dumps(response)
    user_cat_col = USER_CATALOGS_COL.find_one({'user': user["_id"], "_id": catalog_id})
    print(user_cat_col)
    resume_file = CATALOG_FILES_COL.find_one({"_id": file_id, 'catalog': user_cat_col["_id"]})
    print(resume_file)
    if resume_file:
        file_path = os.path.join(UPLOAD_FILE_PATH, str(resume_file["catalog"]), resume_file["file_name"])
        return send_file(file_path, as_attachment=True)
    else:
        response = {
            "status": "error",
            "message": "File does not exist."
        }
    return json.dumps(response)


@app.route('/activate_deactivate_file', methods=["POST"])
def activate_deactivate_file():
    req_data = request.get_json()
    user_id = ObjectId(str(req_data['user_id']))
    file_id = ObjectId(str(req_data['file_id']))
    is_active = req_data['is_active']
    response = {"status": "", "message": ""}
    user_doc = USERS_COL.find_one({"_id": user_id})
    if user_doc:
        resume_doc = CATALOG_FILES_COL.find_one({"_id": file_id})
        if resume_doc:
            resume_catalog_doc = USER_CATALOGS_COL.find_one({"_id": resume_doc["catalog_id"]})
            if resume_catalog_doc:
                if resume_catalog_doc["user_id"] == user_doc["_id"]:
                    CATALOG_FILES_COL.update_one({"_id": resume_doc["_id"]}, {"$set": {"is_active": is_active}})
                    response["status"] = "success"
                    response["message"] = "Record updated successfully"
                else:
                    response["status"] = "error"
                    response["message"] = "You are not authorized to update this file"
            else:
                response["status"] = "error"
                response["message"] = "File Catalog '{}' does not exist".format(resume_doc["catalog_id"])
        else:
            response["status"] = "error"
            response["message"] = "File '{}' does not exist".format(file_id)
    else:
        response["status"] = "error"
        response["message"] = "User ID '{}' does not exist".format(user_id)

    return json.dumps(response)


if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0", port=5000)
    app.run(debug=True)
