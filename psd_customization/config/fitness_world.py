# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
        {
            "label": _("Gym"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Gym Member",
                    "label": "Member",
                },
            ]
        },
        {
            "label": _("Setup"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Gym Settings",
                    "label": "Gym Settings",
                },
            ]
        },
    ]