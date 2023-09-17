from pathlib import Path

DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
MAIN_DOC_URL = 'https://docs.python.org/3/'
BASE_DIR = Path(__file__).parent

PEP_DOC_URL = 'https://peps.python.org/'

EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}

STATUS_LIST = ['A', 'D', 'F', 'P', 'R', 'S', 'W', '']