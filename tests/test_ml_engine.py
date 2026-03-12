"""Tests for charonos.ml.engine."""

from charonos.ml.engine import IntentClassifier


def test_classifier_predict_known():
    clf = IntentClassifier()
    assert clf.predict("check status") == "status"
    assert clf.predict("list nodes") == "cluster"


def test_classifier_learn_new_intent():
    clf = IntentClassifier()
    clf.learn("deploy to production", "deploy")
    clf.learn("push to prod", "deploy")
    clf.learn("deploy service", "deploy")
    # After learning several examples the new intent should be recognised
    pred = clf.predict("deploy to production now")
    assert pred == "deploy"


def test_classifier_sample_count_grows():
    clf = IntentClassifier()
    initial = clf.sample_count
    clf.learn("new thing", "new_label")
    assert clf.sample_count == initial + 1


def test_classifier_persistence(tmp_path):
    path = str(tmp_path / "clf.json")
    clf = IntentClassifier(persist_path=path)
    clf.learn("test data", "test_label")
    clf.save()

    clf2 = IntentClassifier(persist_path=path)
    clf2.load()
    assert clf2.sample_count == clf.sample_count
