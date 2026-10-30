import os

def get_interface_state(
    router,
    interface_name,
    netmiko_get=None,
):
    """Return normalized interface status using Netmiko + TextFSM."""
    try:
        if netmiko_get is not None:
            ip_info, descriptions = netmiko_get(router, interface_name)
        else:
            from netmiko import ConnectHandler
            cisco_device = {
                'device_type': 'cisco_ios',
                'host': router,
                'username': os.environ.get("ROUTER_USER", ""),
                'password': os.environ.get("ROUTER_PASS", ""),
            }
            with ConnectHandler(**cisco_device) as ch:
                ip_info = ch.send_command(f"show ip interface {interface_name}", use_textfsm=True)
                descriptions = ch.send_command("show interfaces description", use_textfsm=True)
    except PermissionError:
            return {"status": "error", "result": "authentication_failed"}
    except ConnectionError:
        return {"status": "error", "result": "connection_failed"}
    except Exception:
        return {"status": "error", "result": "backend_failed"}
    if not ip_info or len(ip_info) == 0:
         return {"status": "ok", "result": "not_found", "interface": None}
    else:
        data = ip_info[0]
        ip = data["ip_address"][0]
        prefix = data["prefix_length"][0]
        ipv4 = f"{ip}/{prefix}"
        link_status = data.get("link_status", "").lower()
        if "down" in link_status:
            admin_state = "down"
        else:
            admin_state = "up"
        descriptions_text = None
        loopback_short = interface_name.replace("Loopback", "Lo")
        for d in descriptions:
            port = d.get("port", "")
            if port == interface_name or port == loopback_short:
                descriptions_text = d.get("description")
                break
        return {"status": "ok", "result": "found", "interface": {
                        "name": data["interface"],
                        "ipv4": ipv4,
                        "admin_state": admin_state,
                        "description": descriptions_text
                    }
                }

def delete_interface(
    router,
    interface_name,
    netmiko_delete=None,
):
    """Delete an interface using Netmiko."""
    try:
        if netmiko_delete is not None:
            delete_response = netmiko_delete(router, interface_name)
        else:
            from netmiko import ConnectHandler
            cisco_device = {
                'device_type': 'cisco_ios',
                'host': router,
                'username': os.environ.get("ROUTER_USER", ""),
                'password': os.environ.get("ROUTER_PASS", ""),
            }
            with ConnectHandler(**cisco_device) as ch:
                ch.send_config_set([f"no interface {interface_name}"])
        if delete_response == "deleted":
            return {"status": "ok", "result": "deleted"}
        elif delete_response == "not_found":
            return {"status": "ok", "result": "not_found", "interface": None}
    except PermissionError:
            return {"status": "error", "result": "authentication_failed"}
    except ConnectionError:
        return {"status": "error", "result": "connection_failed"}
    except Exception:
        return {"status": "error", "result": "backend_failed"}
