import logging
from database.mongo_db_admin import get_db_sources, set_group
from vk.API import VK
from settings import settings

class SourceService:

    def __init__(self):
        settings.load_JSON("local_settings.json")
        self.vk = VK(settings)

    def fill_groups_properties(self):
        groups = list(get_db_sources())
        for info in groups:
            try:
                # set anything here if will to add
                if not info.get('type') or not info.get('name') or not info.get('whore_score') or not info.get('id'):
                    info = self.processSource(info)
                    if not info:
                        continue
                    set_group(info)
            except Exception as e:
                logging.error(f"Error updating group: {info}. error: {e}")
        
        # check of groups are banned
        try:
            group_names = [g.get("screen_name") for g in groups]
            groups_info = self.vk.get_groupById(str.join(",", group_names))['result']
            if not groups_info:
                raise Exception("Failed get sources info for ban check")
            for info in groups_info:
                if info.get('deactivated'):
                    info['activated'] = False
                    set_group({"screen_name": info.get("screen_name"), "activated": False, "ban_status": info.get('deactivated')})
        except Exception as e:
            logging.error(f"Error checking group are banned: {info}. error: {e}")

    def processSource(self, info):
        try:
            group_id = self.vk.resolve_screen_name(info['screen_name'])['result']
            info['id'] = group_id
            group_info = self.vk.get_groupById(group_id)['result'][0]
            info['name'] = group_info['name']
            info['type'] = group_info['type']
            if not info.get('whore_score'):
                # set standart here, but don't forget to add manually
                info['whore_score'] = 50
            return info
        except Exception as e:
            logging.error(f"Error resolve source info: " + str(e))
            return None