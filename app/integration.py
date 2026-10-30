"""Part 4 student implementation."""

import yaml

from app.dispatcher import dispatch_request

from app.request_handler import validate_webex_envelope

from app.core import validate_request

def process_request(mentioned_people, attachment_path, bot_person_id):
    # TODO: implement according to Part 4 specification
    error = validate_webex_envelope(mentioned_people, attachment_path, bot_person_id)
    if error is not None:
        return error
    try:
        with open(attachment_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        val_res = validate_request(data)
        if val_res.get("status") != "ok" or val_res.get("result") != "accepted":
            return val_res
        return dispatch_request(data)
    except Exception:
        return {"status": "error", "result": "invalid_yaml"}