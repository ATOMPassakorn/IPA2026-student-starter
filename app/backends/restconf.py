import requests
import os
from app.backends.planning import plan_interface as planning_engine
from ipaddress import IPv4Interface

def get_interface_state(
    router,
    interface_name,
    http_get=None,
):
    """Return normalized interface status using RESTCONF."""
    url = f"https://{router}/restconf/data/ietf-interfaces:interfaces/interface={interface_name}"
    try:
        if http_get is not None:
            response = http_get(url)
        else:
            auth = (os.environ.get("ROUTER_USER", ""), os.environ.get("ROUTER_PASS", ""))
            headers = {"Accept": "application/yang-data+json"}
            response = requests.get(url, auth=auth, headers=headers, verify=False, timeout=10)
        if response.status_code == 404:
            return {"status": "ok", "result": "not_found", "interface": None}
        elif response.status_code == 200:
            data = response.json()
            interfaces = data.get("ietf-interfaces:interface", {})
            if interfaces["enabled"] == True:
                admin_state = "up"
            else:
                admin_state = "down"
            addr_obj = interfaces.get("ietf-ip:ipv4", {}).get("address", [{}])[0]
            ip = addr_obj.get("ip")
            mask = addr_obj.get("netmask")
            cidr_str = str(IPv4Interface(f"{ip}/{mask}"))
            return {
                "status": "ok",
                "result": "found",
                "interface": {
                    "name": interfaces["name"],
                    "ipv4": cidr_str,
                    "description": interfaces["description"],
                    "admin_state": admin_state
                }
            }
    except ConnectionError:
        return {"status": "error", "result": "connection_failed"}
    except PermissionError:
        return {"status": "error", "result": "authentication_failed"}
    except:
        return {"status": "error", "result": "backend_failed"}

def plan_interface(
    router,
    desired_interface,
    http_get=None,
):
    """Return create/update/no_change plan using RESTCONF status."""
    def getter(r, name):
        return get_interface_state(r, name, http_get=http_get)
    return planning_engine(router, desired_interface, getter)

def apply_interface(
    router,
    desired_interface,
    http_put=None,
):
    """Apply complete desired interface state using RESTCONF."""
    loopback_number = int(desired_interface["name"][len("Loopback"):])
    url = f"https://{router}/restconf/data/Cisco-IOS-XE-native:native/interface/Loopback={loopback_number}"
    ipv4=IPv4Interface(desired_interface["ipv4"])
    payload = {
    "Cisco-IOS-XE-native:Loopback": {
        "name": loopback_number,
        "description": desired_interface["description"],
        "ip": {
            "address": {
                "primary": {
                    "address": str(ipv4.ip),
                    "mask": str(ipv4.network.netmask)
                    }
                }
            }
        }
    }
    if desired_interface.get("admin_state") == "down":
        payload["Cisco-IOS-XE-native:Loopback"]["shutdown"] = [None]
    try:
        if http_put is not None:
            response = http_put(url, json=payload)
        else:
            auth = (os.environ.get("ROUTER_USER", ""), os.environ.get("ROUTER_PASS", ""))
            headers = {
                "Accept": "application/yang-data+json",
                "Content-Type": "application/yang-data+json",
            }
            response = requests.put(url, auth=auth, headers=headers, json=payload, verify=False, timeout=10)
        if response.status_code in [200, 201, 204]:
            return {"status": "ok", "result": "applied"}
        elif response.status_code in [401, 403]:
            return {"status": "error", "result": "authentication_failed"}
        else:
            return {"status": "error", "result": "backend_failed"}
    except ConnectionError:
            return {"status": "error", "result": "connection_failed"}
    except PermissionError:
        return {"status": "error", "result": "authentication_failed"}
    except:
        return {"status": "error", "result": "backend_failed"}
