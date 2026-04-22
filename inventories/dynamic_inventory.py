#!/usr/bin/env python3
"""
================================================================
FILE: inventories/dynamic_inventory.py
Mo ta: Dynamic Inventory script – tu dong lay danh sach host
       tu bien moi truong (co the mo rong lay tu API / DB).
Dung:
  ansible-playbook site.yml -i inventories/dynamic_inventory.py
  ./inventories/dynamic_inventory.py --list
  ./inventories/dynamic_inventory.py --host node1
================================================================
"""

import json
import os
import sys


def get_inventory() -> dict:
    """
    Tra ve inventory dang JSON.
    Mo rong: thay phan nay bang goi API / query DB de lay host dong.
    """
    # Doc tu bien moi truong (phu hop CI/CD), fallback ve gia tri mac dinh
    web_host = os.environ.get("INV_WEB_HOST", "192.168.80.139")
    db_host  = os.environ.get("INV_DB_HOST",  "192.168.80.140")
    ssh_user = os.environ.get("INV_SSH_USER", "vagrant")
    ssh_pass = os.environ.get("INV_SSH_PASS", "vagrant")

    inventory = {
        "web": {
            "hosts": ["node1"],
        },
        "db": {
            "hosts": ["node2"],
        },
        "all": {
            "children": ["web", "db"],
            "vars": {
                "ansible_user":               ssh_user,
                "ansible_ssh_pass":           ssh_pass,
                "ansible_become":             True,
                "ansible_become_method":      "sudo",
                "ansible_become_pass":        ssh_pass,
                "ansible_python_interpreter": "/usr/bin/python3",
                "ansible_ssh_common_args":    "-o StrictHostKeyChecking=no",
            },
        },
        "_meta": {
            "hostvars": {
                "node1": {"ansible_host": web_host},
                "node2": {"ansible_host": db_host},
            }
        },
    }
    return inventory


def get_host(hostname: str) -> dict:
    inv  = get_inventory()
    meta = inv.get("_meta", {}).get("hostvars", {})
    return meta.get(hostname, {})


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        print(json.dumps(get_inventory(), indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == "--host":
        print(json.dumps(get_host(sys.argv[2]), indent=2))
    else:
        print(json.dumps(get_inventory(), indent=2))
