"""The fixture provider consumes supplied annotations, never calls a model."""
from backend.core.schemas import EvidenceClaim, SourceWindow
from .claims import extract


class FixtureExtractor:
    def extract(self, window: SourceWindow) -> list[EvidenceClaim]:
        if window.provider != "supplied_fixture" or window.evidence_mode != "synthetic_replay":
            raise ValueError("FixtureExtractor only accepts explicitly supplied synthetic fixtures.")
        return extract(window)
