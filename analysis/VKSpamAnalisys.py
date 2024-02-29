import logging
import re
from dadata import Dadata

from database.mongo_db import get_user_by_id, upsert_user_db
logger = logging.getLogger(__name__)

token = "56b25437c4b89b2a7f48378f89c420da26a76aad"
secret = "ae7370eef9ed11fa24df28fd9c1744f35e809c99"
dadata = Dadata(token, secret)
pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'

class VkSpamAnalisys():
    def extend_users_with_phone_location(self, setting, users):
        cities = setting.get("cities")

        for user in users:
            try:
                db_user = get_user_by_id(user.get('id'))
                if not user.get('info') or db_user.get("phone_regions") or user.get('sex') == 2 or db_user.get('deactivated_time'):
                    continue

                match = re.findall(pattern, user.get("info"))
                if len(match) == 0:
                    continue
                
                phone_regions = []
                for number in match:
                    loc_results = dadata.clean('phone', number)
                    
                    region = loc_results.get('region')
                    if region:
                        phone_regions.append(region)
                        if cities:
                            match_found = any(str.lower(city) in str.lower(region) for city in cities)
                            if not match_found:
                                user['spam_score'] = 70

                if len(phone_regions) > 0:
                    user['phone_regions'] = phone_regions
                    upsert_user_db(user)
                    
            except Exception as e:
                logger.warning(f"Cannot extract phone location from user: {user.get('id')} error: {e}")