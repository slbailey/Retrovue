"""
Contract-aligned application usecases.

CLI commands should call functions from here instead of legacy services.
"""

# Import plan modules to make them available at package level
from . import plan_add
from . import plan_delete
from . import plan_list
from . import plan_show
from . import plan_update