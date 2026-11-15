"""Actual sampled-image OCR and short-lived visible-line identity tracking."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from backend.core.identity import stable_id
from .tools import MediaSetupError


@dataclass(frozen=True)
class OCRLine:
    text: str
    confidence: float
    box: list[float]


class RapidOCRProvider:
    def __init__(self):
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.engine = RapidOCR(intra_op_num_threads=1, inter_op_num_threads=1)
        except (ImportError, OSError, RuntimeError) as error:
            raise MediaSetupError("Chat OCR unavailable. Run python scripts/manage.py setup to install rapidocr-onnxruntime and its bundled CPU models. Tesseract is not required. No fixture text is substituted on failure.") from error

    def read(self, image_path) -> list[OCRLine]:
        try:
            result, _ = self.engine(str(image_path))
        except Exception as error:
            raise MediaSetupError(f"OCR failed for sampled frame {image_path.name}: {error}") from error
        lines = []
        for box, text, confidence in result or []:
            text = " ".join(str(text).split())
            if not text:
                continue
            xs, ys = [float(p[0]) for p in box], [float(p[1]) for p in box]
            lines.append(OCRLine(text=text, confidence=max(0., min(1., float(confidence))), box=[min(xs), min(ys), max(xs), max(ys)]))
        return sorted(lines, key=lambda line: (line.box[1], line.box[0]))


def normalized(text: str) -> str:
    return re.sub(r"[^\w]+", " ", text.casefold()).strip()


class VisibleLineTracker:
    """Match only adjacent sampled frames; disappearance permits a new occurrence.

    OCR does not recover native chat IDs. Identical consecutive pixels are necessarily
    ambiguous. Stable visible lines are one observation, not repeated evidence.
    """

    def __init__(self, asset_identity: str):
        self.asset_identity = asset_identity
        self.previous: list[tuple[str, str]] = []

    def update(self, lines: list[OCRLine], media_seconds: float) -> list[tuple[OCRLine, str, bool]]:
        unused = set(range(len(self.previous)))
        current = []
        output = []
        for ordinal, line in enumerate(lines):
            norm = normalized(line.text)
            best = None
            score = .90
            for index in sorted(unused):
                similarity = SequenceMatcher(None, norm, self.previous[index][0]).ratio()
                if similarity > score or (similarity == 1 and score == 1 and best is None):
                    best, score = index, similarity
            is_new = best is None
            if best is None:
                track_id = stable_id("ocr-track", self.asset_identity, media_seconds, ordinal, norm)
            else:
                unused.remove(best)
                track_id = self.previous[best][1]
            current.append((norm, track_id))
            output.append((line, track_id, is_new))
        self.previous = current
        return output
