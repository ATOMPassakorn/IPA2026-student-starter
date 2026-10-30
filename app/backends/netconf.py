import os
import xml.etree.ElementTree as ET
from app.backends.planning import plan_interface as planning_engine
from ipaddress import IPv4Interface

def get_interface_state(
    router,
    interface_name,
    netconf_get_config=None,
):
    """Return normalized interface status using NETCONF."""
    filter_xml = f"""
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
        <name>{interface_name}</name>
    </interface>
    </interfaces>
    """
    try:
        if netconf_get_config is not None:
            xml_text = netconf_get_config(router, filter_xml)
        else:
            from ncclient import manager
            with manager.connect(
                host=router,
                port=830,
                username=os.environ.get("ROUTER_USER", ""),
                password=os.environ.get("ROUTER_PASS", ""),
                hostkey_verify=False
            ) as m:
                m.get_config(source='running', filter=('subtree', filter_xml)).data_xml
        root = ET.fromstring(xml_text)
        namespace = {
            "ietf-if": "urn:ietf:params:xml:ns:yang:ietf-interfaces",
            "ietf-ip": "urn:ietf:params:xml:ns:yang:ietf-ip",
        }
        interface = root.find(".//ietf-if:interface", namespace)
        if interface is None:
            return {"status": "ok", "result": "not_found", "interface": None}
        else:
            name_element = interface.find("ietf-if:name", namespace)
            if name_element is not None:
                name = name_element.text
            else:
                name = interface_name
            description_element = interface.find("ietf-if:description", namespace)
            if description_element is not None:
                description = description_element.text
            else:
                description = None
            enabled_element = interface.find("ietf-if:enabled", namespace)
            if enabled_element is not None and enabled_element.text == "true":
                admin_state = "up"
            else:
                admin_state = "down"
            ip_element = interface.find(".//ietf-ip:ip", namespace)
            mask_element = interface.find(".//ietf-ip:netmask", namespace)
            if ip_element is not None and mask_element is not None:
                cidr_str = str(IPv4Interface(f"{ip_element.text}/{mask_element.text}"))
            else:
                cidr_str = None
            return {"status": "ok", "result": "found", "interface": {
                    "name": name,
                    "description": description,
                    "admin_state": admin_state,
                    "ipv4": cidr_str
                }
            }
    except PermissionError:
        return {"status": "error", "result": "authentication_failed"}
    except ConnectionError:
        return {"status": "error", "result": "connection_failed"}
    except Exception:
        return {"status": "error", "result": "backend_failed"}

def plan_interface(
    router,
    desired_interface,
    netconf_get_config=None,
):
    """Return create/update/no_change plan using NETCONF status."""
    def getter(r, name):
                return get_interface_state(r, name, netconf_get_config=netconf_get_config)
    return planning_engine(router, desired_interface, getter)


def apply_interface(
    router,
    desired_interface,
    netconf_edit_config=None,
):
    """Apply complete desired interface state using NETCONF."""
    loopback_number = int(desired_interface["name"][len("Loopback"):])
    ipv4 = IPv4Interface(desired_interface["ipv4"])
    if desired_interface.get("admin_state") == "down":
        shutdown_xml = "<shutdown/>"
    else:
        shutdown_xml = ""
    config_xml = f"""
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                <interface>
                    <Loopback nc:operation="replace">
                    <name>{loopback_number}</name>
                    <description>{desired_interface["description"]}</description>
                    <ip>
                        <address>
                        <primary>
                            <address>{ipv4.ip}</address>
                            <mask>{ipv4.network.netmask}</mask>
                        </primary>
                        </address>
                    </ip>
                    {shutdown_xml}
                    </Loopback>
                </interface>
            </native>
        </config>
    """
    try:
        if netconf_edit_config is not None:
            netconf_edit_config(router, config_xml)
        else:
            from ncclient import manager
            with manager.connect(
                host=router,
                port=830,
                username=os.environ.get("ROUTER_USER", ""),
                password=os.environ.get("ROUTER_PASS", ""),
                hostkey_verify=False
            ) as m:
                m.edit_config(target='running', config=config_xml)
        return {"status": "ok", "result": "applied"}
    except PermissionError:
            return {"status": "error", "result": "authentication_failed"}
    except ConnectionError:
        return {"status": "error", "result": "connection_failed"}
    except Exception:
        return {"status": "error", "result": "backend_failed"}
