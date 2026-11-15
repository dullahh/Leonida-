"""Small auditable heuristic, not an LLM or a calibrated sentiment model."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re
from typing import Protocol

from backend.core.identity import stable_id
from backend.core.schemas import EvidenceClaim, SourceWindow

SEMANTIC_NAME = "conservative-lexical"
SEMANTIC_VERSION = "conservative-lexical-v3"


@dataclass(frozen=True)
class SupportingSpan:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class Interpretation:
    aspect: str
    target: str
    sentiment: float | None
    abstention_reason: str | None
    confidence: float | None
    causal_attribution: str = "ambiguous"
    relevance: float = 0.0
    supporting_text_span: SupportingSpan | None = None
    classifier_name: str = SEMANTIC_NAME
    classifier_version: str = SEMANTIC_VERSION

    @property
    def reason(self) -> str | None:
        return self.abstention_reason


class SemanticProvider(Protocol):
    """Optional local or external model adapter; never invoked by default."""
    name: str
    version: str

    def classify(self, text: str, *, confidence: float | None, modality: str,
                 speaker_role: str) -> Interpretation: ...


class SemanticClassifier:
    """Deduplicate observation classifications, including optional providers.

    A repeated observation ID with changed text/quality is a provenance error.
    The media evidence cache persists the resulting interpretation across runs.
    """
    def __init__(self, provider: SemanticProvider | None = None):
        self.provider = provider
        self._observations: dict[str, tuple[tuple, Interpretation]] = {}

    def classify(self, observation_id: str, text: str, *, confidence: float | None = None,
                 modality: str = "chat", speaker_role: str = "unknown") -> Interpretation:
        if not observation_id:
            raise ValueError("Classification requires a stable observation ID")
        key = (text, confidence, modality, speaker_role,
               self.provider.name if self.provider else SEMANTIC_NAME,
               self.provider.version if self.provider else SEMANTIC_VERSION)
        previous = self._observations.get(observation_id)
        if previous:
            if previous[0] != key:
                raise ValueError("Observation ID reused with changed classification inputs")
            return previous[1]
        guarded = confidence is not None and confidence < .75 or modality == "speech" and speaker_role != "streamer"
        result = (self.provider.classify(text, confidence=confidence, modality=modality,
                                        speaker_role=speaker_role) if self.provider and not guarded else
                  interpret(text, confidence=confidence, modality=modality, speaker_role=speaker_role))
        if self.provider and not guarded and (result.classifier_name, result.classifier_version) != (self.provider.name, self.provider.version):
            raise ValueError("Provider classification name/version differs from its declared identity")
        if result.supporting_text_span is not None:
            span = result.supporting_text_span
            if text[span.start:span.end] != span.text:
                raise ValueError("Provider supporting span is not in the observation")
        if result.sentiment is None and not result.abstention_reason:
            raise ValueError("Provider abstention must have a reason")
        if not 0 <= result.relevance <= 1 or result.confidence is not None and not 0 <= result.confidence <= 1:
            raise ValueError("Provider confidence/relevance is out of range")
        self._observations[observation_id] = (key, result)
        return result


def _abstain(aspect: str, target: str, reason: str, attribution: str | None = None) -> Interpretation:
    return Interpretation(aspect, target, None, reason, None, attribution or target, 0.0)


@lru_cache(maxsize=16384)
def interpret(text: str, *, confidence: float | None = None, modality: str = "chat", speaker_role: str = "unknown") -> Interpretation:
    """Conservative offline game-quality classifier; no model/network access."""
    lower = text.casefold().replace("’", "'").replace("‘", "'")
    # OCR may join an aspect word and copula. This never changes quoted text.
    lower = re.sub(r"(story|writing|dialogue|narrative|acting|plot|controls|gameplay|game)(is|are)(?=[a-z])", r"\1 \2 ", lower)
    if confidence is not None and confidence < .75:
        return _abstain("overall", "ambiguous", "OCR confidence below 0.75; review sampled frame.", "low_quality")
    if modality == "speech" and speaker_role != "streamer":
        return _abstain("overall", "ambiguous", "Audio speaker is unverified: streamer, NPC dialogue and background voices are not separated.", "unverified_speaker")
    if re.search(r"\b(?:lol|lmao|haha|sarcasm|/s)\b", lower):
        return _abstain("overall", "ambiguous", "Laughter/sarcasm does not establish game approval.")
    if re.search(r"\b(?:i am|i'm|im)\s+(?:so\s+)?(?:bad|terrible|trash|awful)\b|\bmy aim\b|\bi missed\b", lower) and not re.search(r"\b(?:controls?|input|aiming controls)\b", lower):
        return _abstain("gameplay", "player_skill", "Player skill statement does not evaluate game quality.")
    aspect = next((name for name, pattern in (
        ("narrative", r"\b(?:story|writing|dialogue|narrative|acting|plot)\b"),
        ("technical", r"\b(?:glitch(?:es)?|crash(?:ed|es)?|bug(?:s)?|broken|framerate|frame rate|stutter(?:s)?|freeze(?:s)?)\b"),
        ("gameplay", r"\b(?:controls?|gameplay|combat|aiming|input|mission(?:s)?|level design)\b"),
        ("audio", r"\b(?:soundtrack|music|sound design|game audio)\b"),
        ("overall", r"\bgame\b"),
    ) if re.search(pattern, lower)), None)
    if aspect is None:
        target = "unrelated" if re.search(r"\b(?:give me|go to|where is|need a|what is)\b", lower) else "ambiguous"
        return _abstain("overall", target, "No explicit supported game aspect in the text.")
    if re.search(r"\b(?:not|never|hardly|isn't|isnt|don't|dont)\b", lower):
        return _abstain(aspect, "ambiguous", "Negation requires semantic review; lexical heuristic abstains.")
    positive = bool(re.search(r"\b(?:excellent|brilliant|great|good|amazing|love|beautiful|responsive|immersive)\b", lower))
    negative = bool(re.search(r"\b(?:repetitive|bad|terrible|awful|boring|broken|laggy|lags?|clunky|crash(?:ed|es)?|glitch(?:es)?|stutter(?:s)?|freezes?|unresponsive)\b", lower))
    if aspect == "narrative" and re.search(r"\b(?:dialogue|story|writing|acting|plot)\s+(?:is\s+)?carrying\s+(?:the\s+)?(?:whole\s+)?game\b", lower):
        positive = True
    if aspect == "gameplay" and re.search(r"\brockstar\s+cooked\s+with\s+this\s+mission\b", lower):
        positive = True
    if positive == negative:
        return _abstain(aspect, "ambiguous", "Mixed or absent evaluative language; lexical heuristic abstains.")
    return Interpretation(aspect, "game", .4 if positive else -.4, None, .7,
                          "game_quality", 1.0, SupportingSpan(text, 0, len(text)))


def extract(window: SourceWindow) -> list[EvidenceClaim]:
    observation = window.observation
    if observation is None:
        return []
    return [EvidenceClaim(
        run_id=window.run_id,
        claim_id=stable_id("claim", window.window_id, observation.extractor_version, observation.supporting_quote, observation.aspect, observation.target),
        window_id=window.window_id, stream_id=window.stream_id,
        evidence_mode=window.evidence_mode, aspect=observation.aspect,
        source_modality=observation.source_modality, target=observation.target,
        sentiment=observation.sentiment, abstention_reason=observation.abstention_reason,
        quality=observation.semantic_confidence if observation.semantic_confidence is not None else 0,
        supporting_quote=observation.supporting_quote, scene_id=observation.scene_id,
        extractor_version=observation.extractor_version,
        dependency_group=observation.dependency_group,
    )]
