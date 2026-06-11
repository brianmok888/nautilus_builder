"""Evidence ledger errors."""
from __future__ import annotations


class EvidenceError(Exception):
    """Base evidence ledger error."""


class EvidenceNotFoundError(EvidenceError):
    """Evidence reference not found."""


class EvidenceHashMismatchError(EvidenceError):
    """Evidence hash verification failed."""


class EvidenceScopeMismatchError(EvidenceError):
    """Evidence does not belong to the expected project/scope."""
