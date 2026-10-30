from app.planner import build_plan
def plan_interface(
    router,
    desired_interface,
    get_interface_state,
):
    """Build a Part 2 plan from backend status."""
    status_response = get_interface_state(router,desired_interface["name"])
    current_interface = {}
    if status_response["status"] == "error":
        return status_response
    elif status_response["result"] == "not_found":
        current_interface = None
    elif status_response["result"] == "found":
        current_interface = status_response["interface"]
    return build_plan(desired_interface, current_interface)