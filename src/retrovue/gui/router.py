from .features.importers.page import ImportersPage
from .features.schedules.page import SchedulesPage
from .features.content_sources.page import ContentSourcesPage

PAGES = [
    {"title": "Content Sources", "factory": ContentSourcesPage},
    {"title": "Importers", "factory": ImportersPage},
    {"title": "Schedules", "factory": SchedulesPage},
]

