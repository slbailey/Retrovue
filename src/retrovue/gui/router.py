from .features.importers.page import ImportersPage
from .features.schedules.page import SchedulesPage

PAGES = [
    {"title": "Importers", "factory": ImportersPage},
    {"title": "Schedules", "factory": SchedulesPage},
]

