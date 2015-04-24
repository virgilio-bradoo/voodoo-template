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
        'prestashoperpconnect_export_bom_stock',
        'prestashoperpconnect_export_price',
        'multi_company_supplier',
        'sale_intercompany_auto',
        'account_invoice_intercompany',
        'email_template',
    ],
    'data': [
        'views/data.xml',
        'views/invoice.xml',
        'views/prestashop.xml',
        'views/stock.xml',
        'views/sale.xml',
        'security/checkpoint.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
