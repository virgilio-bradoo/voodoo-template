# -*- coding: utf-8 -*-
{
    'name': 'Logistfilex customs',
    'version': '1',
    'category': 'Client',
    'description': """
Add customizations for Logistiflex
""" ,
    'author': 'Arthur Vuillard',
    'website': 'http://www.akretion.com',
    'depends': [
        'prestashoperpconnect',
        'multi_company_supplier',
        'sale_intercompany_auto',
        'account_invoice_intercompany',
    ],
    'data': [
        'views/invoice.xml',
        'views/prestashop.xml',
        'views/stock.xml',
        'security/checkpoint.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
