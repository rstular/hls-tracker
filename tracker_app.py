import json
import re

import redis
import uwsgi

from flask import Flask

def load_json_file(filename):
    with open(filename, "r") as f:
        data = f.read()
    return json.loads(data)

class TrackerApp(Flask):
    # Stateful redis object - placeholder
    redis_obj = None
    # Regex matching function
    valid_stream = None
    # Tracker configuration
    tracker_config = None

    def __init__(self, *args, **kwargs):
        # Load app configuration
        app_config = load_json_file(uwsgi.opt["app-config-file"])

        # Load tracker configuration
        self.tracker_config = app_config["tracker"]

        # Configure stream regex matching function
        self.valid_stream = lambda text : bool(re.compile(app_config["stream_regex"]).search(text))

        # Configure redis connection
        redis_config = app_config["redis"]
        self.redis_obj = redis.Redis(host=redis_config["host"], port=redis_config["port"], db=redis_config["db"])

        # Initialize flask app
        super().__init__(*args, **kwargs)

