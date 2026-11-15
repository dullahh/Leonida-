"""Text-only reaction telemetry from immutable cached observations.

Intensity is a lexical activity heuristic, never measured vocal arousal. Raw
observations and the supported-claim classifier are not modified. Only existing
supported quality claims can cross the separately configured pricing gate.
"""
from functools import lru_cache
import re

from .config import read_config
from .identity import digest, stable_id
from .schemas import ReactionSignal

REACTION_VERSION = "text-reactions-v1"


def reaction_policy():
    return read_config("reaction_policy.json")


@lru_cache(maxsize=32768)
def _text_signal(text, ocr_confidence, source_reason):
    lower = text.casefold().replace("\u2019", "'")
    if ocr_confidence is not None and ocr_confidence < .75:
        return "uncertain", None, None, .0, "unknown", None, "Low OCR confidence; reaction cannot be interpreted reliably."
    if source_reason and re.search(r"compression|repeated asr|asr quality|decoding loop", source_reason, re.I):
        return "uncertain", None, None, .0, "unknown", None, "ASR quality warning; repetition is not reaction intensity."
    if re.search(r"\b(?:i'm|i am|im)\s+(?:so\s+)?(?:bad|terrible|awful)|\bmy aim\b|\bi missed\b|\bi slipped\b", lower):
        return "negative", .65, "frustration", .9, "player_skill", .6, None
    target, certainty = "unknown", .2
    if re.search(r"\b(?:officer|citizen|kill a cop|give me the gun)\b", lower):
        target, certainty = "role_play", .7
    elif re.search(r"\b(?:john|bobby|you did|he's|his|him)\b", lower):
        target, certainty = "another_player", .65
    elif re.search(r"\b(?:got it|what happened|knocked|died)\b", lower):
        target, certainty = "in_game_event", .65
    if re.search(r"\b(?:can't bro|cannot|so frustrating|so annoying|i hate this)\b", lower):
        return "negative", .8, "frustration", certainty, target, .55, None
    if re.search(r"\b(?:what happened|what is happening|i'm confused)\b", lower):
        return "uncertain", .65, "confusion", certainty, target, .55, None
    if re.search(r"\b(?:oh my god|oh man|what the (?:fuck|hell)|wow)\b", lower):
        return "uncertain", .75, "surprise", certainty, target, .55, None
    if re.search(r"\b(?:let's go|lets go|yay|amazing|i got it right)\b", lower):
        return "positive", .75, "excitement", certainty, target, .6, None
    if re.search(r"\b(?:lol|lmao|haha)\b", lower):
        return "uncertain", .55, "amusement", certainty, target, .5, None
    # Profanity/upper-case text alone establishes neither emotion nor valence.
    if "!" in text or re.search(r"\b(?:fuck|shit)\b", lower):
        return "uncertain", .4, None, certainty, target, .4, "Emphasis alone does not establish emotion or game approval."
    return "uncertain", .1, None, certainty, target, .35, "No clear reaction cue in the extracted text."


def pricing_gate(claim, target, target_certainty, relevance, policy):
    if claim is None or claim.sentiment is None or claim.target != "game":
        return False, "No supported game-quality claim; contextual reaction only."
    if target != "game_quality" or target_certainty < policy["minimum_target_certainty"]:
        return False, "Game-quality target attribution is below the configured threshold."
    confidence = claim.semantic_confidence if claim.semantic_confidence is not None else claim.quality
    if confidence < policy["minimum_claim_confidence"]:
        return False, "Supported-claim confidence is below the configured threshold."
    if relevance < policy["minimum_market_relevance"]:
        return False, "Aspect has no configured relevance to this market."
    return True, None


def build_reactions(windows, claims, policy=None):
    policy = policy or reaction_policy()
    by_window = {c.window_id: c for c in claims}
    seen, output = {}, []
    for window in windows:
        # One reaction per immutable observation, independent of delivery count.
        identity = window.observation_id
        fingerprint = digest(window.model_dump(mode="json"))
        if identity in seen:
            if seen[identity] != fingerprint:
                raise ValueError("Reaction observation ID reused with changed source input")
            continue
        seen[identity] = fingerprint
        observation = window.observation
        source_reason = observation.abstention_reason if observation else None
        valence, intensity, emotion, certainty, target, confidence, reason = _text_signal(window.raw_text, window.ocr_confidence, source_reason)
        claim = by_window.get(window.window_id)
        supported = claim is not None and claim.sentiment is not None and claim.target == "game"
        relevance = 0.0
        source_quality_failed = intensity is None and confidence is None
        if supported and not source_quality_failed:
            target, certainty = "game_quality", .95
            valence = "positive" if claim.sentiment > 0 else "negative" if claim.sentiment < 0 else "neutral"
            confidence = claim.semantic_confidence if claim.semantic_confidence is not None else claim.quality
            intensity = .4 if intensity is None else max(.4, intensity)
            reason = None
            relevance = 1.0 if claim.aspect in policy["routed_aspects"] else 0.0
        eligible, exclusion = pricing_gate(claim, target, certainty, relevance, policy)
        output.append(ReactionSignal(run_id=window.run_id,
            reaction_id=stable_id("reaction", window.run_id, identity, REACTION_VERSION, digest(policy)),
            observation_id=identity, window_id=window.window_id, stream_id=window.stream_id, asset_id=window.asset_id,
            evidence_mode=window.evidence_mode, media_seconds=window.source_media_seconds, media_end_seconds=observation.media_end_seconds if observation else None, replay_seconds=window.replay_seconds,
            available_replay_seconds=observation.available_replay_seconds if observation and observation.available_replay_seconds is not None else window.replay_seconds,
            valence=valence, intensity=intensity, emotion=emotion, target_certainty=certainty, likely_target=target,
            source_modality=window.source_modality, confidence=confidence, supporting_text=window.raw_text,
            abstention_reason=reason, exclusion_reason=exclusion,
            supported_claim_id=claim.claim_id if supported else None, market_relevance=relevance,
            pricing_eligible=eligible, classifier_version=REACTION_VERSION, policy_version=policy["policy_version"]))
    return output


