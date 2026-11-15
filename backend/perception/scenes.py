"""Manual scene/dependency labels; visual similarity never establishes identity."""
from collections import defaultdict
from collections.abc import Sequence

from backend.core.schemas import EvidenceClaim


def scene_membership(claims: Sequence[EvidenceClaim]) -> dict[str, tuple[str, ...]]:
    """Group explicitly named manual scenes in one run without inferring identity.

    Unknown labels remain ungrouped. Membership is for inspection, not evidence
    independence or an additional source-weight multiplier. Revisions replace an
    older interpretation of the same claim instead of duplicating membership.
    """
    if len({claim.run_id for claim in claims}) > 1:
        raise ValueError("Manual scene membership cannot mix runs.")
    current = {}
    for claim in claims:
        previous = current.get(claim.claim_id)
        if previous is not None and previous.revision == claim.revision and previous != claim:
            raise ValueError("Conflicting claim content at the same manual scene revision.")
        if previous is None or claim.revision > previous.revision:
            current[claim.claim_id] = claim
    groups = defaultdict(set)
    for claim in current.values():
        if claim.scene_id.strip().casefold() in {"manual-unassigned", "unknown", "unassigned"}:
            continue
        groups[claim.scene_id].add(claim.claim_id)
    return {scene: tuple(sorted(ids)) for scene, ids in sorted(groups.items())}
