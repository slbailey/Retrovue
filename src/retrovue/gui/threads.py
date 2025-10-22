"""
Generic QThread worker helper for running long operations without blocking the UI.
"""

from PySide6.QtCore import QThread, Signal, QObject


class WorkerSignals(QObject):
    """Signals emitted by the worker thread."""
    
    progress = Signal(dict)  # Progress updates (e.g., {"stage": "...", "msg": "..."})
    error = Signal(str)      # Error message
    finished = Signal()      # Operation completed


class Worker(QThread):
    """
    Generic worker thread that runs a generator function and emits signals.
    
    The generator should yield progress dicts like:
        {"stage": "connect", "msg": "Connecting to server..."}
    
    On error, it should raise an exception.
    """
    
    def __init__(self, generator_func, *args, **kwargs):
        """
        Args:
            generator_func: A callable that returns a generator yielding progress dicts
            *args, **kwargs: Arguments to pass to generator_func
        """
        super().__init__()
        self.generator_func = generator_func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._is_cancelled = False
    
    def run(self):
        """Execute the generator function and emit signals."""
        try:
            generator = self.generator_func(*self.args, **self.kwargs)
            
            for progress_dict in generator:
                if self._is_cancelled:
                    break
                self.signals.progress.emit(progress_dict)
            
            if not self._is_cancelled:
                self.signals.finished.emit()
                
        except Exception as e:
            self.signals.error.emit(str(e))
    
    def cancel(self):
        """Request cancellation of the worker."""
        self._is_cancelled = True

