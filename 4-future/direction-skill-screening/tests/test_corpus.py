import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pytest

from src import corpus
from src.screen import CLASSES


def test_corpus_loads_and_validates():
    records = corpus.load()
    assert 12 <= len(records) <= 16
    assert corpus.validate_all(records) == len(records)


def test_corpus_is_synthetic_true():
    assert corpus.is_synthetic() is True
    assert corpus.stats()["is_synthetic"] is True


def test_every_class_appears_in_corpus():
    by_class = corpus.stats()["by_class"]
    for c in CLASSES:
        assert by_class.get(c, 0) >= 1, f"class {c} not represented"


def test_corpus_has_benign_and_adversarial():
    s = corpus.stats()
    assert s["benign"] >= 3
    assert s["adversarial"] >= 3


def test_all_sources_are_authored_synthetic():
    for r in corpus.load():
        assert r["source"] == "authored-synthetic"


def test_validation_rejects_missing_required_field():
    schema = corpus.load_schema()
    bad = dict(corpus.load()[0])
    del bad["manifest"]
    with pytest.raises(corpus.ValidationError):
        corpus.validate_record(bad, schema)


def test_validation_rejects_unknown_class():
    schema = corpus.load_schema()
    bad = dict(corpus.load()[0])
    bad["label"] = {"malicious": True, "classes": ["not_a_real_class"]}
    with pytest.raises(corpus.ValidationError):
        corpus.validate_record(bad, schema)


def test_validation_rejects_adversarial_but_benign():
    schema = corpus.load_schema()
    bad = dict(corpus.load()[0])
    bad["label"] = {"malicious": False, "classes": []}
    bad["adversarial_techniques"] = ["homoglyph_substitution"]
    with pytest.raises(corpus.ValidationError):
        corpus.validate_record(bad, schema)


def test_prior_version_present_for_creep_cases():
    creep = [r for r in corpus.load()
             if "privilege_creep" in r["label"]["classes"]]
    assert creep
    for r in creep:
        assert r["prior_version"] is not None
