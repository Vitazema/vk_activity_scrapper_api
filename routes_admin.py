import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import pymongo
from database.mongo_db_admin import delete_setting, get_db_settings, get_db_sources, set_db_setting, set_group
from database.mongo_db_admin import delete_source, edit_source, get_db_source
from routes import app, getUniqueCites
from spider.sources import SourceService

cors = CORS(app, resources={r"/sources": {"origins": "*", "expose_headers": "Content-Range"}, r"/settings": {"origins": "*", "expose_headers": "Content-Range"}})
sourceService = SourceService()

@app.route('/sources')
def getSources():
    filter = {}
    filter_request = request.args.get("filter")
    sort = json.loads(request.args.get("sort"))
    range = json.loads(request.args.get("range"))
    sort = [(sort[0], pymongo.DESCENDING if sort[1] == "DESC" else pymongo.ASCENDING)]

    if filter_request:
        filter_data = json.loads(filter_request)
        if filter_data.get("setting_id"):
            filter = {"setting_id": int(filter_data.get("setting_id"))}

    sources = list(get_db_sources(filter))
        # Create a response
    response = jsonify(sources)
    
    # Set Content-Range header
    response.headers['Content-Range'] = f'sources 0-{len(sources)-1}/{len(sources)}'
    
    return response

@app.route('/sources/<id>')
def getSource(id):
    source = get_db_source(id)    
    return source

@app.route('/sources/<id>', methods=["DELETE"])
def deleteSource(id):
    delete_source(id)
    return {"message": "Source deleted successfully."}, 200

@app.route('/sources/<id>', methods=["PUT"])
def editSource(id):
    source = request.json
    edit_source(source)
    return source, 200

@app.route('/sources', methods=["POST"])
def createSource():
    screen_name = request.json.get("screen_name")
    whore_score = request.json.get("whore_score")
    setting_id = request.json.get("setting_id")
    activated = request.json.get("activated")
    screen_name = screen_name.rsplit('/', 1)[-1]
    source = {"screen_name": screen_name, "whore_score": whore_score, "setting_id": int(setting_id), "activated": activated}
    source_info = sourceService.processSource(source)
    if not source_info:
        return {"message": "Source cannot be added."}, 400
    set_group(source_info)
    return source_info, 200

@app.route('/getcities', methods=["GET"])
def getCities():
    unique_cities = getUniqueCites()
    unique_cities.insert(0, "_UNDEFINED")
    return unique_cities
    
@app.route('/settings')
def getSettings():
    filter = {}
    filter_request = request.args.get("filter")
    if (filter_request):
        filter = json.loads(filter_request)
    settings = get_db_settings(filter)
    # Create a response
    response = jsonify(settings)
    
    # Set Content-Range header
    response.headers['Content-Range'] = f'settings 0-{len(settings)-1}/{len(settings)}'
    return response

@app.route('/settings/<id>')
def getSetting(id):
    setting = get_db_settings({"id": int(id)})[0]
    return setting

@app.route('/settings', methods=["POST"])
def createSetting():
    name = request.json.get("name")
    activated = request.json.get("activated")
    minutes_delay = request.json.get("minutes_delay")
    days_dept_time_analize = request.json.get("days_dept_time_analize")
    settings = get_db_settings()
    id = len(settings) + 1
    if name in [setting.get("name") for setting in settings]:
        return {"message": "Setting cannot be added: duplicated names"}, 400

    setting = {"name": name, "id": id, "activated": activated, "minutes_delay": minutes_delay, "days_dept_time_analize": days_dept_time_analize}

    set_db_setting(setting)
    return setting, 200

@app.route('/settings/<id>', methods=["PUT"])
def setSetting(id):
    setting = request.json

    if not setting:
        return {"message": "No settings provided."}, 400

    # Filtering out fields that are undefined or null
    filtered_setting = {k: v for k, v in setting.items() if v is not None}

    if not filtered_setting:
        return jsonify({"message": "All settings fields are undefined."}), 400

    set_db_setting(filtered_setting)
    return filtered_setting, 200

@app.route('/settings/<id>', methods=["DELETE"])
def deleteSetting(id):
    delete_setting(id)
    return {"message": "Setting deleted successfully."}, 200