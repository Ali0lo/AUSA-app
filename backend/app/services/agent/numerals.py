"""Check that every number in generated text came from the payload the model was given.

Spec §8's contract is by claim type: numbers come from ML or arithmetic, and the LLM
supplies framing, tone and explanation. That is a rule about output, so it has to be
checkable on output -- "the prompt told it not to" is not a control, and this project has
already had to delete three modules that produced plausible numbers nobody could trace.

The failure this catches is not a lying model. It is the ordinary one: a model handed a
cost band of 1,000-4,000 AZN that writes "about 2,500 AZN a year", or handed IELTS 6.0 that
writes "IELTS 6.5, which most universities want". Both read as facts and neither is in the
data.

Deliberately strict, and deliberately dumb. It does no arithmetic of its own, so a genuine
sum the model computed correctly still trips it -- which is the intended outcome: an
arithmetic result should be computed by the service and passed in, not produced in prose.

Not a runtime filter. Wire it as a test over recorded responses, and as a development
assertion. Silently dropping a sentence from a live answer would leave the student reading
an explanation with a hole in it and no indication there was one.
"""

import re
from typing import Any, Iterable, Set, Tuple

# A numeral, with optional thousands separators and an optional fractional part. Deliberately
# does not match a leading minus: "-3" in text is nearly always a dash or a range, and the
# quantities in this product are all non-negative.
_NUMERAL = re.compile(r"\d[\d,]*(?:\.\d+)?")

# Numerals that never need payload support. Every one is a token that reads as a quantity to
# the regex but is not a claim about the student: ordinals and small counts the model uses
# to structure an answer ("two ways to open it", "1."), and percentages of nothing.
# Kept tiny on purpose -- an allowlist is where a guard goes to die.
_ALWAYS_ALLOWED = frozenset({"0", "1", "2", "3"})


def _normalise(raw: str) -> str:
    """`1,200` -> `1200`, `7.0` -> `7`, `6.50` -> `6.5`.

    Both sides go through this, so a payload float of 7.0 supports a text "7.0" and a text
    "7" equally -- the model should not fail the check for formatting a number the way a
    person would write it.
    """
    text = raw.replace(",", "").strip()
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def numerals_in(text: str) -> Tuple[str, ...]:
    """Every numeral in a piece of text, normalised, in order of appearance."""
    return tuple(_normalise(match.group()) for match in _NUMERAL.finditer(text))


def _walk(value: Any) -> Iterable[str]:
    """Every numeral anywhere in a payload, however nested.

    Strings are mined too, not just numbers. A citation reads 'EU Directive 2019/790' and a
    gate reads '2,800 documented hours'; those numbers are part of what the model was given
    and quoting them back is correct. Booleans are skipped -- `True` is an `int` subclass in
    Python and would otherwise support a bare "1" in the text.
    """
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield _normalise(str(value))
    elif isinstance(value, str):
        for match in _NUMERAL.finditer(value):
            yield _normalise(match.group())
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(key)
            yield from _walk(item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _walk(item)


def supported_numerals(payload: Any) -> Set[str]:
    """The set of numerals a generated answer is allowed to contain."""
    return set(_walk(payload)) | set(_ALWAYS_ALLOWED)


def unsupported_numerals(text: str, payload: Any) -> Tuple[str, ...]:
    """Numerals in `text` that the payload does not support, in order, without duplicates.

    Empty means the text is clean. A non-empty result is a bug in the generated answer, not
    a warning: each entry is a quantity presented to a student that nothing produced.
    """
    allowed = supported_numerals(payload)
    seen: Set[str] = set()
    out = []
    for numeral in numerals_in(text):
        if numeral not in allowed and numeral not in seen:
            seen.add(numeral)
            out.append(numeral)
    return tuple(out)


def assert_numerals_supported(text: str, payload: Any) -> None:
    """Raise if the text carries a number the payload does not.

    The message names the offending numerals, because "an unsupported number" sends whoever
    reads the failure back to diff two blobs by eye.
    """
    unsupported = unsupported_numerals(text, payload)
    if unsupported:
        raise ValueError(
            "Generated text contains numbers the payload does not support: "
            + ", ".join(unsupported)
            + ". Every number shown to a student must come from a model, from arithmetic, "
            "or from a cited page (spec §8)."
        )
