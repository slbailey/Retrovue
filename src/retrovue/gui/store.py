"""
Shared UI state for the application.
"""


class Store:
    """Application-wide state container."""
    
    def __init__(self):
        self.selected_channel_id = 1
        self.toasts = []
        # Add more shared state as needed during migration


# Singleton store instance
store = Store()

