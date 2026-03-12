"""Lightweight ML engine for CharonOS.

Provides basic machine-learning capabilities so the agent can learn from
its interactions — e.g. classifying user intent, clustering past tasks,
and improving response quality over time.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Online-learning intent classifier.

    Uses TF-IDF + SGD so it can be incrementally updated as the agent
    sees more user messages.
    """

    # Built-in seed intents so the classifier is useful from the start
    SEED_DATA: list[tuple[str, str]] = [
        ("check status", "status"),
        ("how are you", "status"),
        ("what is your status", "status"),
        ("show cluster", "cluster"),
        ("list nodes", "cluster"),
        ("cluster info", "cluster"),
        ("run command", "execute"),
        ("execute on node", "execute"),
        ("add api key", "config"),
        ("add ssh host", "config"),
        ("set email", "config"),
        ("grow", "growth"),
        ("upgrade tier", "growth"),
        ("what tier am I on", "growth"),
        ("help", "help"),
        ("what can you do", "help"),
        ("hello", "greeting"),
        ("hey", "greeting"),
        ("good morning", "greeting"),
    ]

    def __init__(self, persist_path: Optional[str] = None) -> None:
        self.persist_path = persist_path
        self._texts: list[str] = []
        self._labels: list[str] = []
        self._pipeline: Optional[Pipeline] = None
        self._seed()

    def _seed(self) -> None:
        for text, label in self.SEED_DATA:
            self._texts.append(text)
            self._labels.append(label)
        self._rebuild()

    def _rebuild(self) -> None:
        if len(set(self._labels)) < 2:
            self._pipeline = None
            return
        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer()),
            ("clf", SGDClassifier(loss="log_loss", random_state=42)),
        ])
        self._pipeline.fit(self._texts, self._labels)

    def predict(self, text: str) -> str:
        """Return the predicted intent label for *text*."""
        if self._pipeline is None:
            return "unknown"
        return self._pipeline.predict([text])[0]

    def learn(self, text: str, label: str) -> None:
        """Add a new training example and retrain."""
        self._texts.append(text)
        self._labels.append(label)
        self._rebuild()
        logger.info("ML: learned new example → '%s' = %s", text[:60], label)

    @property
    def label_count(self) -> int:
        return len(set(self._labels))

    @property
    def sample_count(self) -> int:
        return len(self._texts)

    def save(self, path: Optional[str] = None) -> None:
        target = path or self.persist_path
        if not target:
            return
        data = {"texts": self._texts, "labels": self._labels}
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_text(json.dumps(data))

    def load(self, path: Optional[str] = None) -> None:
        target = path or self.persist_path
        if not target:
            return
        p = Path(target)
        if not p.is_file():
            return
        data = json.loads(p.read_text())
        self._texts = data["texts"]
        self._labels = data["labels"]
        self._rebuild()
