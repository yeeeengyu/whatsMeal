from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class ApiWorker(QRunnable):
    def __init__(self, job):
        super().__init__()
        self._job = job
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self._job()
        except Exception as exc:
            self.signals.failed.emit(str(exc))
            return

        self.signals.finished.emit(result)
