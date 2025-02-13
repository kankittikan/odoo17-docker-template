{
    'name': 'Document Previewer',
    'summary': '''
        Document previewer module for PDF and XLSX.
    ''',
    'author': 'Kittikan Makphon',
    'category': 'Hidden',
    'version': '17.0',
    'license': 'LGPL-3',
    'data' : [
        'security/ir.model.access.csv',
        'views/pdf_previewer.xml',
        'views/xlsx_previewer.xml',
        'data/ir_cron_data.xml'
    ],

    'depends': ['base']
}