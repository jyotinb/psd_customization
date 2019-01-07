# -*- coding: utf-8 -*-
# Copyright (c) 2019, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cint
from builtins import str
import json
from toolz import merge, pluck


@frappe.whitelist()
def set_trainings_in_salary_slip(doc_json, set_in_response=0):
    doc = frappe.get_doc(json.loads(doc_json)) \
        if isinstance(doc_json, str) else doc_json
    if not doc.salary_structure:
        joining_date, relieving_date = frappe.db.get_value(
            'Employee', doc.employee, ['date_of_joining', 'relieving_date']
        )
        doc.salary_structure = doc.check_sal_struct(
            joining_date, relieving_date
        )
    structure = frappe.get_doc('Salary Structure', doc.salary_structure)
    doc.salary_slip_based_on_training = \
        structure.salary_slip_based_on_training
    doc.set('trainings', [])
    if doc.salary_slip_based_on_training:
        trainings = get_trainings_for_salary_slip(
            doc.employee, doc.end_date
        )
        for row in trainings:
            doc.append('trainings', {
                'training': row.name,
                'member_name': row.gym_member_name,
                'months': row.months,
                'subscription': row.gym_subscription,
            })
        doc.total_training_months = sum(pluck('months', trainings))
        doc.training_rate = structure.training_monthly_rate
        add_earning_for_training(
            doc,
            structure.training_salary_component,
            doc.total_training_months * doc.training_rate
        )
    if cint(set_in_response):
        frappe.response.docs.append(doc)


def get_trainings_for_salary_slip(employee, end_date):
    trainer = frappe.db.exists('Gym Trainer', {
        'employee': employee
    })
    if not trainer:
        return []
    trainings = frappe.db.sql(
        """
            SELECT
                ta.name AS name,
                s.member_name AS gym_member_name,
                s.name AS gym_subscription,
                ta.salary_till AS salary_till,
                ta.from_date AS from_date,
                ta.to_date AS to_date,
                s.day_fraction AS day_fraction
            FROM `tabTrainer Allocation` AS ta
            LEFT JOIN `tabGym Subscription` AS s
                ON s.name = ta.gym_subscription
            WHERE
                ta.gym_trainer = %(trainer)s AND
                IFNULL(
                    ta.salary_till,
                    DATE_SUB(ta.from_date, INTERVAL 1 DAY)
                ) < %(end_date)s
        """,
        values={
            'trainer': trainer,
            'end_date': end_date,
        },
        as_dict=1,
    )
    return map(_set_days(end_date), trainings)


def add_earning_for_training(doc, salary_component, amount):
    for row in doc.earnings or []:
        if row.salary_component == salary_component:
            row.amount = amount
            return
    doc.append('earnings', {
        'salary_component': salary_component,
        'abbr': frappe.db.get_value(
            'Salary Component', salary_component, 'salary_component_abbr'
        ),
        'amount': amount,
    })


def _set_days(end_date):
    def fn(row):
        from_date = row.salary_till + 1 if row.salary_till else row.from_date
        to_date = min(getdate(end_date), row.to_date)
        days = (to_date - from_date).days + 1
        return frappe._dict(
            merge(row, {
                'months': days * row.day_fraction,
            })
        )
    return fn