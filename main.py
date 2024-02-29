import argparse
import logging.handlers
import os
import sys
from time import sleep

from flask import jsonify

from routes import app
import routes_admin
import routes_insta

MAIN_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(MAIN_DIR, 'irequests/'))
sys.path.insert(0, os.path.join(MAIN_DIR, 'settings/'))
sys.path.insert(0, os.path.join(MAIN_DIR, 'vk/'))
sys.path.insert(0, os.path.join(MAIN_DIR, 'inst/'))
sys.path.insert(0, os.path.join(MAIN_DIR, 'analysis/'))

from settings import settings
from spider.spider import Spider

IS_DEVELOPMENT = os.environ.get('ENVIRONMENT') != 'production'

def cli_args_parser_init():
    """
    Осуществляет инициализацию парсера аргументов коммандной строки
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--settings",
        action="store",
        dest="SETTING_FILE_NAME",
        help="File with settigs",
        type=str)
    parser.add_argument(
        "-l",
        "--log",
        action="store",
        dest="LOG_FILE_NAME",
        help="File with logs",
        type=str)
    return parser

def log_init():
    # logging.disable(logging.DEBUG)
    # logging.basicConfig(level=logging.INFO)
    if IS_DEVELOPMENT:
        settings.log_level = logging.DEBUG
    root_logger = logging.getLogger()
    root_logger.setLevel(level=settings.log_level)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level=settings.log_level)
    console.setFormatter(logging.Formatter(settings.log_format))
    handler = logging.handlers.RotatingFileHandler(
        settings.log_file, 
        maxBytes=settings.log_max_bytes_in_file, 
        encoding=settings.encoding)
    handler.setFormatter(logging.Formatter(settings.log_format))
    root_logger.addHandler(handler)
    root_logger.addHandler(console)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("irequests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# adjusted flask_logger
def flask_logger(bot_process):
    global running
    # Create empty job.log, old logging will be deleted
    open("app/job.log", 'w').close()

    """creates logging information"""
    with open("app/job.log") as log_info:
        while bot_process.is_alive():
            data = log_info.read()
            yield data.encode()
            sleep(1)
    bot_process.join()
    running = False

def init_app():
    # parse cli arguments
    parser = cli_args_parser_init()
    cli_args = parser.parse_args()
    # init settings
    if cli_args.SETTING_FILE_NAME:
        settings.load_JSON(cli_args.SETTING_FILE_NAME)
    # init log
    if cli_args.LOG_FILE_NAME:
        settings.log_file = cli_args.LOG_FILE_NAME  
    log_init()

if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not IS_DEVELOPMENT:
    init_app()
    spider = Spider(settings, working_hours=(6, 24))
    spider.start()
    app.spider = spider

@app.route("/bot", methods=["GET"])
def stream():
    """run bot"""
    global spider
    spider.trigger_task()
    return jsonify({"message": "Bot started successfully."}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=50000, threaded=True, debug=IS_DEVELOPMENT)
