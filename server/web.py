import threading
from flask import Flask

from utils.logger import get_logger

_lock = threading.Lock()
app = Flask("git2svn-sync")
logger = get_logger(__name__)

trigger_counters = {}


def has_trigger_for(name):
    return lambda *args, **kwargs: get_trigger_counter(name).get('counter') > 0


def run():
    app.run(host="0.0.0.0", port=5001)


def initialize(trigger_name, counter=0):
    trigger_counters[trigger_name] = counter


@app.route("/")
def home():
    return "Git <=> SVN Sync Home"


@app.route("/trigger/<name>", methods=['POST'])
def trigger(name):
    logger.info(f"Received trigger for '{name}'")
    if trigger_counters.__contains__(name):
        with _lock:
            count = trigger_counters[name]
            logger.info(f"Current counter for '{name}' = {count}")
            trigger_counters[name] = count + 1
            logger.debug(f"Incremented counted to {trigger_counters[name]}")
            return {'status': 'success'}
    return {'status': 'error', 'message': f'{name} not found'}


@app.route("/trigger/<name>", methods=['GET'])
def get_trigger_counter(name):
    logger.debug("Retrieving trigger counter")
    if trigger_counters.__contains__(name):
        with _lock:
            return {'name': name, 'counter': trigger_counters[name]}
    return {'name': name, 'counter': 0}


@app.route("/trigger/<name>/clear", methods=['POST'])
def clear_trigger_counter(name):
    logger.debug("Clearing trigger counter")
    if trigger_counters.__contains__(name):
        with _lock:
            count = trigger_counters[name]
            trigger_counters[name] = 0
            logger.info(f"Cleared trigger counter, was {count}")
    return {'name': name, 'counter': trigger_counters.get(name)}
