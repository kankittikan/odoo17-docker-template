{
    'name' : 'Thaindo Store',
    'depends': ['thaindo_base', 'stock'],
    'data': [
        'securitys/ir.model.access.csv',
        'data/sequence.xml',
        'views/stock_menu.xml',
        'views/product_template.xml',
        'views/stock_remove_create.xml',
        'views/product_import.xml',
        'views/product_request.xml',
        'views/hr_employee.xml',
        'views/product_category.xml',
        'reports/product_request_template.xml',
        'reports/xlsx_report.xml',
        'wizards/xlsxwriter_stock_status_report_view.xml',
        'wizards/xlsxwriter_stock_request_report_view.xml',
        'wizards/xlsxwriter_stock_import_report_view.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}