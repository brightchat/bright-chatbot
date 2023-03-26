import logging
import time


class BasicAppSegmentLogger:
    """
    Class that can be used in a context manager
    to log the execution in a segment of the application.
    """

    def __init__(self, title: str, logger=None, log_level=logging.DEBUG):
        self._title = title
        self._exc_start = None
        self._exc_end = None
        self._logger = logger or logging.getLogger()
        self._log_level = log_level

    def _log_msg(self, message: str, **kwargs):
        self._logger.log(self._log_level, message, **kwargs)

    def log_start_segment(self):
        self._log_msg(f"Starting segment {self.title}")

    def log_end_segment(self):
        msg = "Finished segment '{title}' in {duration:.2f} seconds"
        self._log_msg(msg.format(title=self.title, duration=self.exc_duration))

    def start_segment(self) -> None:
        self.log_start_segment()

    def end_segment(self) -> None:
        self.log_end_segment()

    def __enter__(self):
        self.start_segment()
        self._exc_start = time.perf_counter()
        return self

    def __exit__(self, *args, **kwargs):
        self._exc_end = time.perf_counter()
        self.end_segment()

    @property
    def title(self) -> str:
        """
        Returns the title of the application segment
        """
        return self._title

    @property
    def exc_duration(self) -> float:
        """
        Return the duration of the segment execution in seconds
        """
        if not self._exc_end:
            raise AssertionError("Segment has not been executed")
        return self._exc_end - self._exc_start
