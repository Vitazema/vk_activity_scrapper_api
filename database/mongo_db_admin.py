import datetime
import logging
from . import mongo_db

logger = logging.getLogger(__name__)
db_sources = mongo_db.db.sources
db_settings = mongo_db.db.settings

def get_db_settings(filter={}):
    return list(db_settings.find(filter, {"_id": 0}))

def get_db_setting(name):
    return db_settings.find_one({"name": name}, {"_id": 0})

def set_db_setting(setting):
    return db_settings.update_one({"name": setting.get('name')}, {"$set": setting}, upsert=True)

def delete_setting(id):
    db_settings.delete_one({"id": int(id)})

def get_db_source(id):
    return db_sources.find_one({"id": int(id)}, {"_id": 0})

def delete_source(id):
    db_sources.delete_one({"id": int(id)})

def edit_source(source):
    db_sources.update_one({"id": int(source.get("id"))}, {"$set": source}, upsert=True)

def get_db_sources(filter={}):
    month_ago_unix = datetime.datetime.now() - datetime.timedelta(days=30)
    pipeline = [
        {"$match": filter},
        {"$lookup":
            {
                "from": "activities",
                "localField": "screen_name",
                "foreignField": "owner_domain",
                "as": "activities",
                "pipeline": [
                    {
                        "$project": {
                            "signer_id": 1,
                            "date": 1,
                        },
                    },
                    {
                        "$lookup":
                        {
                            "from": "users",
                            "localField": "signer_id",
                            "foreignField": "id",
                            "as": "signer_details",
                            "pipeline": [
                                {
                                    "$project": {
                                        "deactivated": 1,
                                        "sex": 1,
                                    },
                                },
                            ],
                        },
                    },
                    {
                        "$match": {
                            "date": {
                                "$gte": month_ago_unix.timestamp(),
                            },
                            "signer_details.sex": { "$eq": 1 },
                            "signer_details.deactivated": { "$eq": "active" }
                        },
                    },
                ],
            }
        },
        {
            "$addFields": {
                "female_last_month": {
                    "$size": "$activities"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "activities": 0
            }
        }
    ]

    return db_sources.aggregate(pipeline)

def set_group(group):
    try:
        return db_sources.update_one({"screen_name": group["screen_name"]}, {"$set": group}, upsert=True)
    except Exception as e:
        logger.error(f"Failed to update {group} to: {str(mongo_db.db.name)}. Exception: {e}")
