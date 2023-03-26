from utils.loggers import BasicAppSegmentLogger


class MockedXRayAppLogger(BasicAppSegmentLogger):
    """
    An App segment logger that supports AWS XRay Segments
    """

    def __init__(self, title: str, xray_recorder=None, **kwargs):
        super().__init__(title, **kwargs)

    def start_segment(self) -> None:
        super().start_segment()

    def end_segment(self) -> None:
        super().end_segment()
        if self.xray_recorder:
            self.xray_recorder.end_subsegment()
