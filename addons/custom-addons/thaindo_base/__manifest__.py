{
    'name' : 'Thaindo Base',
    'depends': ['base', 'show_ui_menu_id', 'report_xlsx', 'sequence_reset_period', 'document_previewer'],
    'data': [
        'securitys/ir.model.access.csv',
        'reports/paper_format.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}