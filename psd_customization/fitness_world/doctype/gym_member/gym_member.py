# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.contacts.address_and_contact \
    import load_address_and_contact, delete_contact_and_address
from frappe.contacts.doctype.address.address import get_default_address
from frappe.contacts.doctype.contact.contact import get_default_contact
from psd_customization.utils.fp import pick, compact
import operator
from functools import reduce, partial
from toolz import merge, count, first, pluck, get, compose


class GymMember(Document):
    def onload(self):
        load_address_and_contact(self)
        self.load_membership_details()

    def before_save(self):
        self.flags.is_new_doc = self.is_new()
        self.member_name = ' '.join(
            compact([self.first_name, self.last_name])
        )
        if not self.status:
            self.status = 'Active'
        if not self.auto_renew:
            frequency = frappe.db.get_value(
                'Gym Membership Plan', self.membership_plan, 'frequency'
            )
            if frequency == 'Lifetime':
                self.auto_renew = 'No'
            else:
                self.auto_renew = 'Yes'
        if not self.customer:
            self.customer = self.create_customer()
        if not self.notification_contact:
            self.notification_number = None

    def on_update(self):
        if self.flags.is_new_doc:
            self.fetch_and_link_doc('Address', get_default_address)
            self.notification_contact = \
                self.fetch_and_link_doc('Contact', get_default_contact)
            self.save()

    def on_trash(self):
        delete_contact_and_address('Gym Member', self.name)

    def load_membership_details(self):
        all_memberships = frappe.db.sql(
            """
                SELECT
                    si.rounded_total AS amount,
                    ms.status AS status,
                    ms.to_date AS end_date
                FROM `tabGym Membership` AS ms, `tabSales Invoice` AS si
                WHERE
                    ms.docstatus = 1 AND
                    ms.member = '{member}' AND
                    ms.reference_invoice = si.name
                ORDER BY ms.to_date DESC
            """.format(member=self.name),
            as_dict=True,
        )
        unpaid_memberships = filter(
            lambda x: x.get('status') == 'Unpaid', all_memberships
        )
        outstanding = reduce(
            operator.add, pluck('amount', unpaid_memberships), 0
        )
        frequency = frappe.db.get_value(
            'Gym Membership Plan', self.membership_plan, 'frequency'
        )
        frequency = 'Lifetime'
        self.set_onload('membership_details', {
            'total_invoices': count(all_memberships),
            'unpaid_invoices': count(unpaid_memberships),
            'outstanding': outstanding,
            'frequency': frequency,
            'end_date': self.expiry_date,
        })

    def fetch_and_link_doc(self, doctype, fetch_fn):
        docname = fetch_fn('Customer', self.customer)
        if docname:
            doc = frappe.get_doc(doctype, docname)
            doc.append('links', {
                'link_doctype': 'Gym Member',
                'link_name': self.name,
            })
            doc.save()
        return docname

    def create_customer(self):
        field_kwargs = pick([
            'email_id', 'mobile_no',
            'address_line1', 'address_line2',
            'city', 'state', 'pincode', 'country',
        ], self)
        customer_group = frappe.get_value(
            'Gym Settings', None, 'default_customer_group'
        )
        customer = frappe.get_doc(
            merge({
                'doctype': 'Customer',
                'customer_name': self.member_name,
                'customer_type': 'Individual',
                'customer_group': customer_group or 'All Customer Groups',
                'territory': 'All Territories',
            }, field_kwargs)
        ).insert()
        return customer.name

    def update_expiry_date(self):
        try:
            self.expiry_date = compose(
                partial(get, 'to_date'),
                first,
            )(
                frappe.db.sql(
                    """
                        SELECT to_date FROM `tabGym Membership`
                        WHERE docstatus = 1 AND
                            member = '{member}' AND
                            status = 'Paid'
                        ORDER BY to_date DESC
                        LIMIT 1
                    """.format(member=self.name),
                    as_dict=True,
                )
            )
            self.save()
        except StopIteration:
            pass
