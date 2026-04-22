#!/usr/bin/env python3
import json

inventory = {
    "web": {
        "hosts": ["192.168.80.139"],
        "vars": {
            "ansible_user": "vagrant",
            "ansible_ssh_pass": "vagrant",
            "ansible_become": True,
            "ansible_become_method": "sudo",
            "ansible_become_pass": "vagrant",
            "ansible_python_interpreter": "/usr/bin/python3"
        }
    },
    "db": {
        "hosts": ["192.168.80.140"],
        "vars": {
            "ansible_user": "vagrant",
            "ansible_ssh_pass": "vagrant",
            "ansible_become": True,
            "ansible_become_method": "sudo",
            "ansible_become_pass": "vagrant",
            "ansible_python_interpreter": "/usr/bin/python3"
        }
    },
    "_meta": {
        "hostvars": {
            "192.168.80.139": {"ansible_host": "192.168.80.139"},
            "192.168.80.140": {"ansible_host": "192.168.80.140"}
        }
    }
}

print(json.dumps(inventory))
