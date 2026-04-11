"""Shared fakes and fixtures for server tests."""

from __future__ import annotations

from typing import Any

import pytest

from server.services import firestore_db


# ── Firestore fakes ──────────────────────────────────────────────────────────


class FakeDoc:
    """Simulates a Firestore DocumentSnapshot."""

    def __init__(self, doc_id: str, data: dict | None, reference: FakeDocRef | None = None):
        self.id = doc_id
        self._data = data
        self.reference = reference

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict | None:
        return self._data


class FakeDocRef:
    """Simulates a Firestore DocumentReference with subcollection support."""

    def __init__(self, collection_store: dict, doc_id: str):
        self.collection_store = collection_store
        self.doc_id = doc_id

    def get(self) -> FakeDoc:
        return FakeDoc(self.doc_id, self.collection_store.get(self.doc_id), reference=self)

    def collection(self, name: str) -> FakeCollection:
        payload = self.collection_store.setdefault(self.doc_id, {"id": self.doc_id})
        subcollections = payload.setdefault("_subcollections", {})
        sub_store = subcollections.setdefault(name, {})
        return FakeCollection(sub_store)

    def update(self, payload: dict) -> None:
        existing = self.collection_store.setdefault(self.doc_id, {"id": self.doc_id})
        existing.update(payload)


class FakeQuery:
    """Simulates a Firestore query with chained where/order_by."""

    def __init__(self, docs: list[FakeDoc]):
        self.docs = docs

    def where(self, field: str, op: str, value: Any) -> FakeQuery:
        return FakeQuery([doc for doc in self.docs if (doc.to_dict() or {}).get(field) == value])

    def order_by(self, field: str) -> FakeQuery:
        return FakeQuery(sorted(self.docs, key=lambda d: (d.to_dict() or {}).get(field, 999999)))

    def stream(self) -> list[FakeDoc]:
        return self.docs


class FakeCollection:
    """Simulates a Firestore CollectionReference."""

    def __init__(self, store: dict):
        self.store = store

    def document(self, doc_id: str) -> FakeDocRef:
        return FakeDocRef(self.store, doc_id)

    def stream(self) -> list[FakeDoc]:
        return [
            FakeDoc(doc_id, data, reference=FakeDocRef(self.store, doc_id))
            for doc_id, data in self.store.items()
        ]

    def where(self, field: str, op: str, value: Any) -> FakeQuery:
        docs = self.stream()
        return FakeQuery(docs).where(field, op, value)


class FakeClient:
    """Simulates a Firestore Client backed by an in-memory dict."""

    def __init__(self, data: dict[str, dict]):
        self.data = data

    def collection(self, name: str) -> FakeCollection:
        return FakeCollection(self.data.setdefault(name, {}))


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def fake_firestore(monkeypatch):
    """Inject a FakeClient into firestore_db and return the backing data dict.

    Tests can populate the returned dict before calling Firestore helpers:

        def test_something(fake_firestore):
            fake_firestore["jobs"]["j1"] = {"id": "j1", ...}
            result = firestore_db.get_job_processed_artifact("j1")
    """
    data: dict[str, dict] = {"jobs": {}, "candidates": {}}
    monkeypatch.setattr(firestore_db, "_client", FakeClient(data))
    return data
