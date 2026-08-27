"""Prototype: tamper-evident, append-only evidence ledger (hash chain).

The AgentShield tagline ends in **Audit**. A governance product should be able
to prove its evidence has not been altered after the fact. This ledger wraps the
existing :class:`EvidenceRecord` stream in a SHA-256 hash chain: each entry binds
the hash of the previous entry, so any edit, deletion, or reordering breaks the
chain and is detectable by :meth:`verify`.

The ledger can persist to a JSONL file (append-only) or stay in memory. It
performs no network I/O and stores no secrets - records are the same
publicly-safe synthetic evidence produced elsewhere in the package.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .models import EvidenceRecord, canonical_hash

GENESIS = "0" * 64


@dataclass
class LedgerEntry:
    seq: int
    prev_hash: str
    record: dict
    entry_hash: str


def _entry_hash(seq: int, prev_hash: str, record: dict) -> str:
    return canonical_hash({"seq": seq, "prev_hash": prev_hash, "record": record})


@dataclass
class VerificationResult:
    valid: bool
    entries: int
    broken_at: Optional[int] = None
    reason: Optional[str] = None


class HashChainedEvidenceStore:
    """Append-only evidence store with a verifiable hash chain.

    Implements the ``AppendOnlyEvidenceStore`` protocol (``append`` / ``all``)
    so it is a drop-in for :class:`InMemoryEvidenceStore` in the workflow.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self._entries: list[LedgerEntry] = []
        self._path = Path(path) if path else None
        if self._path and self._path.exists():
            self._load()

    # -- AppendOnlyEvidenceStore surface ------------------------------------
    def append(self, record: EvidenceRecord) -> LedgerEntry:
        payload = record.to_dict()
        prev = self._entries[-1].entry_hash if self._entries else GENESIS
        seq = len(self._entries)
        entry = LedgerEntry(
            seq=seq,
            prev_hash=prev,
            record=payload,
            entry_hash=_entry_hash(seq, prev, payload),
        )
        self._entries.append(entry)
        if self._path:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(_entry_to_json(entry), sort_keys=True) + "\n")
        return entry

    def all(self) -> list[EvidenceRecord]:
        return [EvidenceRecord(**e.record) for e in self._entries]

    # -- Ledger-specific surface -------------------------------------------
    def entries(self) -> list[LedgerEntry]:
        return list(self._entries)

    def head(self) -> str:
        return self._entries[-1].entry_hash if self._entries else GENESIS

    def __len__(self) -> int:
        return len(self._entries)

    def verify(self) -> VerificationResult:
        """Recompute the chain and report the first broken link, if any."""

        prev = GENESIS
        for i, e in enumerate(self._entries):
            if e.seq != i:
                return VerificationResult(False, len(self._entries), i, "sequence gap")
            if e.prev_hash != prev:
                return VerificationResult(
                    False, len(self._entries), i, "prev_hash mismatch"
                )
            recomputed = _entry_hash(e.seq, e.prev_hash, e.record)
            if recomputed != e.entry_hash:
                return VerificationResult(
                    False, len(self._entries), i, "record tampered"
                )
            prev = e.entry_hash
        return VerificationResult(True, len(self._entries))

    def _load(self) -> None:
        assert self._path is not None
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            self._entries.append(
                LedgerEntry(
                    seq=data["seq"],
                    prev_hash=data["prev_hash"],
                    record=data["record"],
                    entry_hash=data["entry_hash"],
                )
            )


def _entry_to_json(entry: LedgerEntry) -> dict:
    return {
        "seq": entry.seq,
        "prev_hash": entry.prev_hash,
        "record": entry.record,
        "entry_hash": entry.entry_hash,
    }
