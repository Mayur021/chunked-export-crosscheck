"""Cross-check: a reversibility fold against the chunked-export corpus.

One question, asked twelve times. The fold in
`reversibility.chain_reversibility` takes the worst of the declared step
classes. The corpus states, per record, what the composed class of the whole
export actually is. Where the two disagree, the fold is understating.

The disagreements are not failures of this suite. They are the finding, and
they are recorded as strict xfails so that a change on either side which
removes one shows up as an unexpected pass rather than passing silently.
"""
import json
import pathlib

import pytest

from reversibility import ReversibilityClass, chain_reversibility, classify

# The corpus ships inside the installed package, pinned at 0.22.0.
import agent_evidence_vectors as _aev

CORPUS = pathlib.Path(_aev.__file__).parent / "corpora" / "vectors-chunked-export"
MANIFEST = json.loads((CORPUS / "MANIFEST.json").read_text(encoding="utf-8"))

# The corpus a result was recorded against, so a silent swap is visible.
EXPECTED_CORPUS_DIGEST = (
    "8d9e15ebf4e6a6b76960491fff189ccdad8521479fff71de1da8ddc43f22b12a"
)

# The corpus names step classes in its own vocabulary. This maps them onto the
# declared effects the fold classifies, and nothing else is translated: no
# reconstruction semantics, no seal handling, no contract validation. The fold
# is being asked only the question it answers.
STEP_CLASS_TO_DECLARED_EFFECT = {
    "read_only": "read_only",
    "reversible": "recoverable_local",
    "externally_reversible": "externally_recoverable",
    "irreversible": "non_recoverable",
}

COMPOSED_CLASS = {
    "read_only": ReversibilityClass.READ_ONLY,
    "reversible": ReversibilityClass.REVERSIBLE,
    "externally_reversible": ReversibilityClass.EXTERNALLY_REVERSIBLE,
    "irreversible": ReversibilityClass.IRREVERSIBLE,
}

# Six of the twelve, all one cause: every step is labelled reversible, so the
# fold returns reversible, while the export crosses a reconstruction threshold
# and the composed class is irreversible. A maximum over labels cannot express
# "k of n reconstructs the dataset".
#
# Two of the six are the cases the corpus maintainers named, because in those
# the record carries a seal asserting maxClass reversible, so the record states
# the wrong class out loud. The other four are the same gap with nothing
# asserting anything.
UNDERSTATES_BY_THRESHOLD = {
    "variant-a-at-crossing",
    "variant-a-final-chunk",
    "variant-a-max-of-labels-seal",          # named upstream: seal asserts it
    "sets-key-field-chunk-alone",
    "count-same-three-chunks",
    "sets-key-field-max-of-labels-seal",     # named upstream: seal asserts it
}


def _vectors():
    params = []
    for vector in MANIFEST["vectors"]:
        marks = []
        if vector["id"] in UNDERSTATES_BY_THRESHOLD:
            marks.append(
                pytest.mark.xfail(
                    strict=True,
                    reason=(
                        "the fold is a maximum over declared step classes and "
                        "cannot represent composition by reconstruction threshold"
                    ),
                )
            )
        params.append(pytest.param(vector, id=vector["id"], marks=marks))
    return params


def test_corpus_is_the_one_this_result_was_recorded_against():
    assert MANIFEST["corpusDigest"] == EXPECTED_CORPUS_DIGEST
    assert MANIFEST["suite"] == "chunked-export/v1"
    assert len(MANIFEST["vectors"]) == 12


def test_every_named_divergence_exists_in_the_corpus():
    """A renamed or dropped vector must not quietly become a silent pass."""
    ids = {v["id"] for v in MANIFEST["vectors"]}
    missing = UNDERSTATES_BY_THRESHOLD - ids
    assert not missing, "recorded divergences no longer in the corpus: %s" % sorted(missing)


@pytest.mark.parametrize("vector", _vectors())
def test_fold_matches_the_composed_class(vector):
    record = json.loads(
        (CORPUS / vector["path"] / "record.json").read_text(encoding="utf-8")
    )
    effects = [
        STEP_CLASS_TO_DECLARED_EFFECT.get(chunk.get("stepClass"))
        for chunk in record.get("chunks", [])
    ]
    folded = chain_reversibility([classify(effect) for effect in effects])
    assert folded is COMPOSED_CLASS[vector["composedClass"]]
