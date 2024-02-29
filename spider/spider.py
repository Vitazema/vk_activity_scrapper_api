from collections import deque
import logging
import threading
import time
from analysis.VKSpamAnalisys import VkSpamAnalisys
from database.mongo_db import update_index_fields

from database.mongo_db_admin import get_db_settings
from spider.ActivityScrapper import ActivityScrapper
from spider.UserScrapper import UserScrapper
from spider.sources import SourceService
from vk import VK

logger = logging.getLogger(__name__)

global spider

class Spider:
    """ Класс для сбора """
    def __init__(self, app_settings, working_hours=(6,24), interval_delay=60):
        self.vk = VK(app_settings)
        self.settings = app_settings
        self.interval_delay = interval_delay
        self.working_hours = working_hours
        self.thread = threading.Thread(target=self.run_bot)
        self.thread.daemon = True
        self.lock = threading.Lock()
        self.condition = threading.Condition()
        self.userScrapper = UserScrapper(self.vk, app_settings)
        self.activityScrapper = ActivityScrapper(self.vk, app_settings)
        self.spamUserAnalisys = VkSpamAnalisys()
        self.sourceService = SourceService()
        self.api_count_entries = deque()
        self.stats = {"session_number": 0, "api_calls_count_last_24h": 0, "activity_processed": 0, "users_processed": 0}

    def start(self):
        """Start the repeating task thread"""
        self.thread.start()
    
    def run_bot(self):
        """Repeat the task every `interval_delay` seconds"""
        return
        while True:
            with self.condition:
                settings = get_db_settings()
                if settings:
                    # todo: avoid get first setting minute delay
                    self.interval_delay = float(settings[0].get("minutes_delay", 60)) * 60
                logger.info(f"Waiting for {self.interval_delay / 60} mins. until next session. Or trigger manually")
                self.condition.wait(timeout=self.interval_delay)
                if self.is_working_hours():
                    self.execute()
                else:
                    logger.info(f"Now working hours. Sleeping for {self.interval_delay / 60} mins. Or trigger manually")

    def run_session(self):
        """Run the task once"""
        try:
            logger.info("Spider session started")
            self.stats["session_number"] += 1

            # prepare sources:
            self.sourceService.fill_groups_properties()
            settings = get_db_settings({"activated": True})

            for setting in settings:
                # scrap!
                self.stats['activity_processed'] += self.activityScrapper.scrap_activities(setting)
                proceeded_users = self.userScrapper.scrap_users(setting)
                self.stats['users_processed'] += len(proceeded_users)

                # spam filter analisys
                self.spamUserAnalisys.extend_users_with_phone_location(setting, proceeded_users)

            if self.vk.calls_count:
                self.add_value(self.vk.calls_count)
            # reset calls_count
            self.vk.calls_count = 0

            update_index_fields()
            
            logger.info(f"Spider session finished: {self.stats}")
            self.stats['users_processed'] = 0
            self.stats['activity_processed'] = 0
        except Exception as e:
            logger.exception(f"Session failed! {self.stats} Error: {e}")

    def execute(self):
        with self.lock: # only one thread can execute this at once
            self.run_session()
        # Lock will be automatically released after the block

    def is_working_hours(self):
        """Check if current time is in working hours"""
        current_hour = time.localtime().tm_hour
        start, end = self.working_hours
        return start <= current_hour <= end

    def trigger_task(self):
        """Trigger the task to run in the next thread loop"""
        with self.condition:
            logger.info(f"Spider triggered manually!")
            self.execute()
    
    def add_value(self, value):
        current_time = time.time()  # Timestamp in seconds since the epoch
        # Remove entries older than 24 hours
        while self.api_count_entries and self.api_count_entries[0][0] < current_time - 86400:  # 86400 seconds in 24 hours
            _, oldest_value = self.api_count_entries.popleft()
            self.stats["api_calls_count_last_24h"] -= oldest_value

        self.api_count_entries.append((current_time, value))
        self.stats["api_calls_count_last_24h"] += value