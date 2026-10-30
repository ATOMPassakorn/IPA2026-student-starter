from ipaddress import IPv4Interface
import subprocess
import json

def apply_interface(
    router,
    desired_interface,
    run_playbook=None,
):
    """Apply complete desired interface state using Ansible."""
    ipv4 = IPv4Interface(desired_interface["ipv4"])
    variables = {
        "router": router,
        "interface_name": desired_interface["name"],
        "description": desired_interface["description"],
        "ipv4_address": str(ipv4.ip),
        "netmask": str(ipv4.network.netmask),
        "shutdown": desired_interface["admin_state"] == "down",
    }
    extra_vars = json.dumps(variables)
    command = [
        "ansible-playbook",
        "-i", "ansible/inventory.ini",
        "ansible/apply_interface.yml",
        "--extra-vars", extra_vars,
    ]
    try:
        if run_playbook is not None:
            run_playbook(variables)
        else:
            subprocess.run(
                command,
                check=True,
                text=True
            )
        return {"status": "ok", "result": "applied"}
    except PermissionError:
            return {"status": "error", "result": "authentication_failed"}
    except ConnectionError:
        return {"status": "error", "result": "connection_failed"}
    except Exception:
        return {"status": "error", "result": "backend_failed"}
