import yaml

def validate_request(data):
    """
    Validate one IPA2026 desired-state request.

    Return a response dictionary according to
    specs/response-spec-v1.md.
    """
    # TODO: implement
    VALID_COMBINATIONS = {
    "restconf": {"status", "plan", "apply"},
    "netconf": {"status", "plan", "apply"},
    "ansible": {"apply"},
    "netmiko-textfsm": {"status", "delete"},
    }

    if not isinstance(data,dict):
        return {"status": "error", "result": "invalid_yaml"}

    if "version" not in data:
        return {"status": "error", "result": "invalid_version"}
    if data["version"] != 1 or type(data["version"]) is not int:
        return {"status": "error", "result": "invalid_version"}

    if "router" not in data:
        return {"status": "error", "result": "missing_router"}

    if data["router"] not in ["10.0.29.101","10.0.29.102","10.0.29.103"\
    ,"10.0.29.104","10.0.29.105"]:
        return {"status": "error", "result": "invalid_router"}

    if "method" not in data:
        return {"status": "error", "result": "missing_method"}

    if data["method"] not in ["restconf", "netconf", "ansible", "netmiko-textfsm"]:
        return {"status": "error", "result": "invalid_method"}

    if "action" not in data:
        return {"status": "error", "result": "missing_action"}

    action = data["action"]
    allowed_actions = VALID_COMBINATIONS[data["method"]]
    if action not in allowed_actions:
        return {"status": "error", "result": "invalid_action"}

    if "desired" not in data or not isinstance(data["desired"], dict):
        return {"status": "error", "result": "missing_desired"}
    desired = data["desired"]
    if "interface" not in desired or not isinstance(desired["interface"], dict):
        return {"status": "error", "result": "missing_interface"}
    interface = desired["interface"]
    if "name" not in interface or not interface["name"]:
        return {"status": "error", "result": "missing_interface_name"}

    if action in ["plan","apply"]:
        if "ipv4" not in interface:
            return {"status": "error", "result": "missing_ipv4"}
        if "description" not in interface:
            return {"status": "error", "result": "missing_description"}
        if "admin_state" not in interface:
            return {"status": "error", "result": "missing_admin_state"}
        if interface["admin_state"] not in ["up","down"]:
            return {"status": "error", "result": "invalid_admin_state"}

    return {"status": "ok", "result": "accepted"}

def process_request_file(path):
    """
    Read a YAML request file, validate it,
    and return a response dictionary.
    """
    # TODO: implement
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return validate_request(data)
    except Exception:
        return {"status": "error", "result": "invalid_yaml"}
