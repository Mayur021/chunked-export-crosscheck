# chunked-export-crosscheck

A cross-check between two independent projects, recording where they disagree and why.

One side is the reversibility fold in [`aisvs-c9-action-class-conformance`](https://github.com/Mayur021/aisvs-c9-action-class-conformance), pinned at `v1.3.0`. It takes the worst of the declared step classes across a composed chain. The other is the `chunked-export/v1` corpus in [`agent-evidence-vectors`](https://github.com/probityai/agent-evidence-vectors), pinned at `0.22.0`, which states for each of twelve records what the composed class of the whole export actually is.

This repository exists because that comparison belongs in neither project. The fold's own suite says the core holds no producer-specific semantics, and the corpus is not a test of anybody's model. What a cross-check records is a relationship between two releases, so it gets its own place and its own pins.

## The result

Six of twelve agree. Six diverge, and all six have one cause.

| | |
|---|---|
| agree | `variant-a-below-threshold`, `threshold-committed-after-first-chunk`, `sets-three-chunks-no-reconstructing-set`, `step-class-irreversible`, `contract-id-missing`, `contract-id-unknown` |
| diverge | `variant-a-at-crossing`, `variant-a-final-chunk`, `variant-a-max-of-labels-seal`, `sets-key-field-chunk-alone`, `count-same-three-chunks`, `sets-key-field-max-of-labels-seal` |

In every one of the six, each chunk is labelled `reversible`, so a maximum over the step classes returns reversible, while the export crosses a reconstruction threshold and the composed class is irreversible. Three chunks of five where `k` is three reconstruct the dataset; one chunk that is a minimal set on its own does the same.

**The fold cannot express this, and that is the finding.** Composition here is not a maximum over labels. It is a threshold over a set, and a maximum has no way to say "k of n reconstructs the whole". The fold's own documentation makes the right argument, that a sequence of individually reversible steps can reach an irreversible outcome no single step shows, and then implements it as `max`, which is sufficient for a chain whose worst step is the worst outcome and insufficient here.

Two of the six, `variant-a-max-of-labels-seal` and `sets-key-field-max-of-labels-seal`, are the cases the corpus maintainers named. In those the record carries a seal asserting `maxClass: reversible`, so the record states the wrong class out loud and the corpus expects a verifier to deny on `seal_understates_composition`. The other four are the same gap with nothing asserting anything, which is the quieter and more dangerous half.

## What this is not

It is not a conformance claim about either project. The fold is asked only the question it answers, which is the composed class given the declared step classes. Nothing here translates reconstruction semantics, evaluates a seal, or validates a contract identifier, so the six agreements are not evidence that the fold would pass as a chunked-export verifier. It would not, and it is not trying to be one.

It is also not a defect report against the corpus. The corpus is right on all twelve.

## Pins, and why both are exact

Both sides are pinned exactly rather than floored, because the result means something only against named releases.

`agent-evidence-vectors` is held at `0.22.0` with bumps reviewed by hand rather than taken automatically, because the `sets` rule and the order of the seal and composition checks are both marked Proposed upstream. Re-checked on 2026-10-26: `chunkedexport.py` and the entire `vectors-chunked-export` tree are byte-identical across the `0.22.0`, `0.25.0` and `0.26.0` wheels, at `072277af9336` and `25bd3f11ca62` over 42 files, with `MANIFEST.json` identical at `72c42c7594`. So the pin is not holding anything back.

The fold is pinned at `v1.3.0` rather than tracking `main`, so a model change shows up as a deliberate re-pin and a restated result rather than quietly moving the record.

`tests/test_crosscheck.py` also asserts the corpus digest, so a swap underneath the pin is visible rather than silent.

## Running it

```bash
pip install -e ".[test]"
pytest -v
```

Expect six passes, six strict xfails and two guard tests. A strict xfail means that if a change on either side removes a divergence, the run fails with an unexpected pass rather than going green, which is the point: the six are a record, not a tolerance.

## License

Apache-2.0.
