def build_plan(desired_interface, current_interface):
    """
    Compare desired interface state with normalized current state
    and return a plan according to specs/plan-spec-v1.md.
    """
    # TODO: implement
    if current_interface is None:
        return {
            "status": "ok",
            "result": "planned",
            "operation": "create",
            "changes": {
                "ipv4": {
                    "to": desired_interface["ipv4"]
                },
                "description": {
                        "to": desired_interface["description"]
                },
                "admin_state": {
                        "to": desired_interface["admin_state"]
                }
            }
        }
    changes = {}
    managed_fields = ["ipv4", "description", "admin_state"]
    for fileld in managed_fields:
        if fileld in desired_interface and desired_interface[fileld] != current_interface[fileld]:
            changes[fileld]= {"from": current_interface[fileld], 
                           "to": desired_interface[fileld]}
    if current_interface is not None:
        if len(changes) > 0:
            return {
                "status": "ok",
                "result": "planned",
                "operation": "update",
                "changes": changes
            }
        else:
            return {
                "status": "ok",
                "result": "planned",
                "operation": "no_change",
                "changes": {}
            }