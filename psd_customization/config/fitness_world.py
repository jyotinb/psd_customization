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
                {
                    "type": "doctype",
                    "name": "Gym Membership",
                    "label": "Membership",
                },
            ]
        },
        {
            "label": _("Setup"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Gym Membership Plan",
                    "label": "Membership Plan",
                },
                {
                    "type": "doctype",
                    "name": "SMS Template",
                    "label": "SMS Template",
                },
                {
                    "type": "doctype",
                    "name": "Gym Settings",
                    "label": "Gym Settings",
                },
            ]
        },
        {
            "label": _("Reports"),
            "items": [
                {
                    "type": "report",
                    "is_query_report": True,
                    "name": "Gym Membership Status",
                    "label": "Membership Status",
                },
            ]
        },
    ]
