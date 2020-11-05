import hashlib
import os.path as path
import re
import secrets

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

from tracker_app import TrackerApp

app = TrackerApp(__name__)
CORS(app, supports_credentials=True)

@app.route("/api/stream/stats/<stream>", methods=["GET"])
def handle_stream_info(stream):

    # Check if supplied stream format is valid
    if not app.valid_stream(stream):
        resp = make_response("Not found")
        resp.status_code = 404
        return resp

    # Return number of viewers
    key_iterator = app.redis_obj.scan_iter("{}:{}:*".format(app.tracker_config["redis_key_prefix"], stream))
    key_count = sum(1 for _ in key_iterator)
    
    resp = make_response(jsonify({"count": key_count}))
    resp.status_code = 200
    return resp


@app.route("/api/stream/index/<stream>", methods=["GET"])
def handle_stream_index(stream):

    # Check if supplied stream format is valid
    if not app.valid_stream(stream):
        resp = make_response("Not found")
        resp.status_code = 404
        return resp

    # Check if stream exists
    stream_dir = path.join(app.tracker_config["hls_root_dir"], stream)
    if not path.isdir(stream_dir):
        resp = make_response("Not found")
        resp.status_code = 404
        return resp

    # Get stream content
    with open(path.join(stream_dir, "index.m3u8"), "r") as f:
        index_file_content = f.read()
    resp = make_response(index_file_content)
    resp.status_code = 200
    resp.mimetype = "application/vnd.apple.mpegurl"

    cookie_name = app.tracker_config["cookie"]["prefix"] + stream
    cookie_value = ""
    # Check if tracking cookie exists
    if not cookie_name in request.cookies or len(request.cookies[cookie_name]) == 0:
        user_ip = request.headers["Cf-Connecting-Ip"] if "Cf-Connecting-Ip" in request.headers else request.remote_addr
        random_hex = secrets.token_hex(16)
        
        string_to_hash = app.tracker_config["hash_salt"] + user_ip + stream + random_hex
        cookie_value = hashlib.sha256(string_to_hash.encode()).hexdigest()

        resp.set_cookie(cookie_name, value=cookie_value, max_age=app.tracker_config["cookie"]["expiration"], domain=app.tracker_config["cookie"]["domain"])
    else:
        cookie_value = request.cookies[cookie_name]

    redis_key_name = "{}:{}:{}".format(app.tracker_config["redis_key_prefix"], stream, cookie_value)
    redis_key_value = "1"

    app.redis_obj.set(redis_key_name, redis_key_value, ex=app.tracker_config["dead_threshold"])

    return resp


if __name__ == "__main__":
    app.run(host="localhost", port=3001, debug=True)
