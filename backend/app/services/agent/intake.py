"""Free text in, an assessable profile out -- carrying only what the student actually said.

A 17-year-old does not arrive holding `qualification_held="attestat"`. They arrive saying
*"robototexnika oxumaq istəyirəm, DİM balım 520, IELTS 7"*. This module turns that sentence
into the same fields `POST /routes/assess` takes, so the "based on own interest" half of the
product has an entrance that is not a form.

**Every extraction is anchored.** A number is only ever claimed when a token naming its field
sits next to it: `520` becomes a DİM score because the word DİM is beside it, never because
520 looks like a DİM score. A message of bare numerals yields nothing. This is the single
rule that separates reading from guessing, and it is why this parser is regular expressions
and not a model -- `extract_and_update_profile` invented GPA 3.8 and IELTS 7.5 out of an
unreadable transcript and reported success, and that is the failure this file exists to make
structurally impossible rather than merely discouraged.

Three consequences worth stating, because each one is a place a helpful parser would lie:

**A field stated twice with two values is dropped, not resolved.** "I got 6.5, then 7" may
mean a retake or a typo. Picking the higher one flatters the student into a route; picking
the lower one closes one. The field comes back in `conflicts` for the student to settle.

**A subject never becomes a field group.** "Robotics" is engineering, the DİM ixtisas qrupu
for engineering is 1, and Group 1's Dövlət Proqramı threshold is 400 against 550 for
everything else. Inferring the group from the subject would move a real gate by 150 points on
the strength of a word. `interest` is carried through as uninterpreted text and decides
nothing; `dim_field_group` is set only when the student names a group.

**A grade without its scale is not read as a grade.** Same rule as the registration form
(app/domain/grades.py): 4.5 is excellent out of 5 and impossible out of 4.

What this returns is a reading, not a decision. `still_needed` and `worth_asking` say what to
ask next; nothing is defaulted to make the profile look complete.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.tools import tool

# Azerbaijani letters folded to their ASCII neighbours so one pattern matches "DİM balım"
# and "DIM balim". Every replacement is one character for one character, and `_fold` keeps
# it that way, because every quote reported below is sliced out of the ORIGINAL text using a
# span found in the folded copy -- the student must read back their own sentence, dots and
# all, not a transliteration of it.
_FOLD = str.maketrans(
    {
        "İ": "I", "ı": "i", "Ə": "E", "ə": "e", "Ö": "O", "ö": "o",
        "Ü": "U", "ü": "u", "Ğ": "G", "ğ": "g", "Ş": "S", "ş": "s",
        "Ç": "C", "ç": "c",
    }
)


def _fold(text: str) -> str:
    """Lowercase and ASCII-fold without moving a single index."""
    out = []
    for char in text.translate(_FOLD):
        lowered = char.lower()
        # A handful of codepoints lowercase into two (ẞ -> ss). Keeping the original there
        # costs a match nobody will miss and preserves the alignment everything else needs.
        out.append(lowered if len(lowered) == 1 else char)
    return "".join(out)


_NUM = r"(\d+(?:[.,]\d+)*)"


def _number(raw: str) -> Optional[float]:
    """`2,800` and `2.800` are two thousand eight hundred; `6,5` and `6.5` are six and a half.

    Separator followed by exactly three digits is a thousands mark, anything else is a
    decimal. No field in this domain is quoted to three decimal places, so the one genuinely
    ambiguous case cannot arise here.
    """
    compact = raw.replace(" ", "")
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", compact):
        return float(re.sub(r"[.,]", "", compact))
    compact = compact.replace(",", ".")
    if compact.count(".") > 1:
        return None
    try:
        return float(compact)
    except ValueError:
        return None


@dataclass(frozen=True)
class _NumberRule:
    """One anchored number. `pattern` must hold exactly one group, and it is the number.

    `low`/`high` are the range the field is published on, and they are load-bearing rather
    than defensive: they are what stops "I sat the IELTS" from being read as an SAT score.
    """
    field: str
    pattern: str
    low: float
    high: float
    integer: bool = False


_NUMBER_RULES: Tuple[_NumberRule, ...] = (
    _NumberRule("dim_score", r"\bdim\b\D{0,20}" + _NUM, 0, 700),
    _NumberRule("dim_score", _NUM + r"\s*bal\b", 0, 700),
    _NumberRule("ielts", r"\bielts\b\D{0,15}" + _NUM, 0, 9),
    _NumberRule("toefl", r"\btoefl\b\D{0,15}" + _NUM, 0, 120, integer=True),
    # "I sat 3 exams" cannot become an SAT score: the published range starts at 400.
    _NumberRule("sat", r"\bsat\b\D{0,12}" + _NUM, 400, 1600, integer=True),
    _NumberRule("act", r"\bact\b\D{0,12}" + _NUM, 1, 36, integer=True),
    _NumberRule("tr_yos", r"\b(?:tr[- ]?)?yos\b\D{0,15}" + _NUM, 0, 100),
    _NumberRule("test_as", r"\btest[- ]?as\b\D{0,15}" + _NUM, 0, 200),
    _NumberRule("hsk", r"\bhsk\b\D{0,10}" + _NUM, 1, 6, integer=True),
    # Azerbaijani puts the number on either side of the noun -- "19 yaşım var" and
    # "yaşım 19-dur" are the same sentence.
    _NumberRule("age", r"\b" + _NUM + r"\s*yas", 14, 80, integer=True),
    _NumberRule("age", r"\byas\w{0,6}\D{0,4}" + _NUM, 14, 80, integer=True),
    _NumberRule("age", r"\b(?:i am|i'?m|aged|age)\D{0,4}" + _NUM, 14, 80, integer=True),
    _NumberRule("age", r"\b" + _NUM + r"\s*years?\s*old\b", 14, 80, integer=True),
    _NumberRule(
        "work_experience_hours",
        _NUM + r"\s*(?:saat|hours?|hrs)\b",
        1, 100000, integer=True,
    ),
    # Only when the student names the group. Never from the subject they named.
    _NumberRule("dim_field_group", r"\b" + _NUM + r"[- ]?(?:ci|cu|ci)?\s*qrup", 1, 4, integer=True),
    _NumberRule("dim_field_group", r"\b(?:qrup|group)\D{0,3}" + _NUM, 1, 4, integer=True),
)

# What the student is going FOR, which is not always what they hold. "I finished my
# bachelor's and want a master's" names both, and the intent verb is what tells them apart.
_INTENT = (
    r"(?:want|wanna|would like|plan|planning|hoping|apply|applying|study|studying|"
    r"looking for|isteyir|istiyir|oxumaq|niyyet|davam)"
)

_LEVEL_WORDS: Tuple[Tuple[str, str], ...] = (
    ("bachelor", r"\b(?:bachelor'?s?|bakalavr|undergraduate|lisans)\b"),
    ("master", r"\b(?:master'?s?|magistr|magistratura)\b"),
)

# What they hold NOW. Deliberately narrower than the level words: "a bachelor's" is a level,
# "a bachelor's degree" is a qualification, and the difference is the whole answer for
# Germany and the UK.
_QUALIFICATION_WORDS: Tuple[Tuple[str, str], ...] = (
    ("attestat", r"\battestat"),
    (
        "bachelor_degree",
        r"\b(?:bachelor'?s? degree|bakalavr diplom|bakalavri bitir|bakalavr pilles[ie]ni bitir"
        r"|b\.?sc\b|graduated from (?:a )?universit)",
    ),
    ("a_level", r"\ba[- ]?levels?\b"),
    ("ib", r"\b(?:ib|ibdp|international baccalaureate)\b"),
    (
        "one_year_university",
        r"\b(?:one year (?:of|at|in) (?:a )?universit|1 il universitet|birinci kurs"
        r"|first year (?:of|at) universit)",
    ),
    ("foundation_year", r"\bfoundation (?:year|programme|program)\b"),
    ("feststellungspruefung", r"\bfeststellung"),
)

_CEFR = re.compile(r"\b([abc][12])\b")
_CEFR_ANCHOR = re.compile(
    r"(?:german|deutsch|alman|english|ingilis|dil\b|language|cefr|level|seviyy|sertifikat|goethe|telc)"
)

# A grade only travels with its scale, so the scale has to be in the sentence.
_GPA = re.compile(
    r"\b" + _NUM + r"\s*(?:/|out of|uzerinden|dan\b|den\b)\s*(100|5|4)\b"
)
_BARE_GRADE = re.compile(r"\b(?:gpa|orta bal|attestat bal)\D{0,8}" + _NUM)
_GPA_SCALES = {"5": ("5.0", 5.0), "4": ("4.0", 4.0), "100": ("100", 100.0)}

_MONEY = re.compile(_NUM + r"\s*(?:azn|manat|₼)\b")
_PER_YEAR = re.compile(r"(?:per year|a year|annually|il[- ]?d[ei]|her il|ilde|/\s*il|/\s*year)")

_INTEREST = re.compile(
    r"(?:study|studying|major in|majoring in|interested in|specialise in|specialize in)\s+"
    r"([a-z][a-z\- ]{2,40})"
)
_INTEREST_AZ = re.compile(r"([a-z][a-z\- ]{2,40}?)\s+(?:uzre\s+)?oxumaq")
_INTEREST_TAIL = {
    "in", "at", "abroad", "for", "and", "the", "a", "to", "of", "xaricde", "istEyirEm",
    "isteyirem", "program", "programme", "degree", "my", "i", "with", "on",
}

# Fields no pattern here reads, listed so the caller can see the omission is deliberate.
# `employer` gates SOCAR and is a free-text company name with no anchor to hang on; the
# olympiad medal and the international-medal flag are booleans, and a boolean read out of
# prose is one "I don't have" away from being backwards.
_NOT_PARSED = ("employer", "has_international_olympiad_medal", "csca")

_REQUIRED = ("level_sought", "qualification_held")


@dataclass(frozen=True)
class Heard:
    """One extracted value and the words it was read from."""
    field: str
    value: Any
    quote: str


@dataclass(frozen=True)
class Intake:
    fields: Dict[str, Any]
    heard: Tuple[Heard, ...]
    conflicts: Tuple[str, ...]
    interest: Optional[str]
    still_needed: Tuple[str, ...]
    worth_asking: Tuple[str, ...]
    notes: Tuple[str, ...]

    @property
    def ready_to_assess(self) -> bool:
        """Both fields `/routes/assess` requires are present. Nothing here supplies them."""
        return not self.still_needed


def _collect(
    candidates: Dict[str, List[Tuple[Any, str]]],
    field: str,
    value: Any,
    quote: str,
) -> None:
    candidates.setdefault(field, []).append((value, quote))


def _numbers(folded: str, text: str, candidates: Dict[str, List[Tuple[Any, str]]],
             notes: List[str]) -> None:
    for rule in _NUMBER_RULES:
        for match in re.finditer(rule.pattern, folded):
            value = _number(match.group(1))
            if value is None:
                continue
            if not (rule.low <= value <= rule.high):
                # Said, and outside the range the field is published on. Reported rather
                # than clamped: a DİM of 850 is a mistake worth telling the student about,
                # and silently storing 700 would answer a question they did not ask.
                notes.append(
                    f"{match.group(0).strip()} reads as {rule.field} but {value:g} is "
                    f"outside its published range ({rule.low:g}-{rule.high:g}), so it was "
                    f"not used. Ask the student to confirm the number."
                )
                continue
            _collect(candidates, rule.field, int(value) if rule.integer else value,
                     text[match.start():match.end()].strip())


def _words(folded: str, text: str, candidates: Dict[str, List[Tuple[Any, str]]]) -> None:
    for value, pattern in _QUALIFICATION_WORDS:
        for match in re.finditer(pattern, folded):
            _collect(candidates, "qualification_held", value,
                     text[match.start():match.end()].strip())

    # Levels get one extra pass: a level word introduced by an intent verb wins outright,
    # so "I finished my bachelor's and want a master's" resolves to master rather than
    # coming back as a conflict.
    intended: List[Tuple[str, str]] = []
    seen: List[Tuple[str, str]] = []
    for value, pattern in _LEVEL_WORDS:
        for match in re.finditer(pattern, folded):
            quote = text[match.start():match.end()].strip()
            seen.append((value, quote))
            window = folded[max(0, match.start() - 40):match.start()]
            if re.search(_INTENT, window):
                intended.append((value, quote))

    chosen = intended if len({v for v, _ in intended}) == 1 else seen
    for value, quote in chosen:
        _collect(candidates, "level_sought", value, quote)


def _cefr(folded: str, text: str, candidates: Dict[str, List[Tuple[Any, str]]]) -> None:
    for match in _CEFR.finditer(folded):
        window = folded[max(0, match.start() - 30):match.end() + 30]
        if _CEFR_ANCHOR.search(window):
            _collect(candidates, "language_certificate_level", match.group(1).upper(),
                     text[match.start():match.end()].strip())


def _grade(folded: str, text: str, candidates: Dict[str, List[Tuple[Any, str]]],
           notes: List[str]) -> None:
    found = False
    for match in _GPA.finditer(folded):
        value = _number(match.group(1))
        scale_key, ceiling = _GPA_SCALES[match.group(2)]
        if value is None or not (0.0 <= value <= ceiling):
            notes.append(
                f"'{match.group(0).strip()}' is not a grade that exists on that scale, so "
                f"it was not used."
            )
            continue
        quote = text[match.start():match.end()].strip()
        _collect(candidates, "gpa", value, quote)
        _collect(candidates, "gpa_scale", scale_key, quote)
        found = True

    if not found and _BARE_GRADE.search(folded):
        notes.append(
            "A grade average was mentioned without saying which scale it is on. 4.5 is "
            "excellent out of 5 and impossible out of 4, so it was not recorded. Ask "
            "whether the scale is 5.0, 100, 4.0 or German."
        )


def _budget(folded: str, text: str, candidates: Dict[str, List[Tuple[Any, str]]]) -> None:
    for match in _MONEY.finditer(folded):
        # A figure in manat is only a yearly budget if the student said yearly. A one-off
        # sum read as an annual one triples their means over a three-year degree.
        if _PER_YEAR.search(folded[max(0, match.start() - 30):match.end() + 30]):
            value = _number(match.group(1))
            if value is not None:
                _collect(candidates, "budget_azn_per_year", value,
                         text[match.start():match.end()].strip())


def _interest(folded: str, text: str) -> Optional[str]:
    for pattern in (_INTEREST, _INTEREST_AZ):
        match = pattern.search(folded)
        if match is None:
            continue
        words = text[match.start(1):match.end(1)].strip().split()
        while words and words[-1].lower().strip(",.") in _INTEREST_TAIL:
            words.pop()
        if words:
            return " ".join(words).strip(" ,.")
    return None


def parse_intake(text: str) -> Intake:
    """Read a student's own sentence into the fields `/routes/assess` takes.

    Nothing is inferred and nothing is defaulted. A field the message does not state is
    absent from `fields`, which is how the engine is told "unknown" rather than "no".
    """
    folded = _fold(text)
    candidates: Dict[str, List[Tuple[Any, str]]] = {}
    notes: List[str] = []

    _numbers(folded, text, candidates, notes)
    _words(folded, text, candidates)
    _cefr(folded, text, candidates)
    _grade(folded, text, candidates, notes)
    _budget(folded, text, candidates)

    fields: Dict[str, Any] = {}
    heard: List[Heard] = []
    conflicts: List[str] = []
    for field_name, found in candidates.items():
        values = {value for value, _ in found}
        if len(values) > 1:
            conflicts.append(field_name)
            quotes = ", ".join(sorted(f"'{quote}'" for _, quote in found))
            notes.append(
                f"{field_name} was stated more than once with different values ({quotes}). "
                f"It was left unset -- ask the student which one is current rather than "
                f"choosing."
            )
            continue
        value, quote = found[0]
        fields[field_name] = value
        heard.append(Heard(field=field_name, value=value, quote=quote))

    still_needed = tuple(name for name in _REQUIRED if name not in fields)

    worth_asking: List[str] = []
    if fields.get("level_sought") == "bachelor" and "age" not in fields:
        worth_asking.append(
            "age -- Türkiye Bursları' bachelor award is limited to under 21, and it is one "
            "of the few open to a school-leaver. Without it that gate stays unknown."
        )
    if "dim_score" in fields and "dim_field_group" not in fields:
        worth_asking.append(
            "dim_field_group (ixtisas qrupu 1-4) -- the Dövlət Proqramı threshold is 400 "
            "for Group 1 and 550 otherwise, so the score alone answers only at the extremes."
        )
    if "gpa" not in fields and "gpa_scale" not in fields:
        worth_asking.append("gpa and gpa_scale -- a grade average, and which scale it is on.")

    return Intake(
        fields=fields,
        heard=tuple(heard),
        conflicts=tuple(sorted(conflicts)),
        interest=_interest(folded, text),
        still_needed=still_needed,
        worth_asking=tuple(worth_asking),
        notes=tuple(notes),
    )


def intake_as_dict(intake: Intake) -> Dict[str, Any]:
    """The reading as JSON, for the agent tool and for `POST /routes/parse`."""
    return {
        "fields": dict(intake.fields),
        "heard": [
            {"field": h.field, "value": h.value, "quote": h.quote} for h in intake.heard
        ],
        "conflicts": list(intake.conflicts),
        "interest": intake.interest,
        "ready_to_assess": intake.ready_to_assess,
        "still_needed": list(intake.still_needed),
        "worth_asking": list(intake.worth_asking),
        "not_parsed": list(_NOT_PARSED),
        "notes": list(intake.notes),
        "instruction": (
            "These are the fields the student's own words support, with the words each one "
            "came from. Anything absent is UNKNOWN, not zero and not absent-therefore-fine: "
            "pass on only what is in `fields`, and ask for what is in `still_needed`. "
            "`interest` is the subject they named, carried through uninterpreted -- it is "
            "not a DİM ixtisas qrupu and must never be turned into one."
        ),
    }


@tool
def read_student_message(message: str) -> Dict[str, Any]:
    """Read a student's free-text message into the fields the route tools take.

    Use this when a student describes themselves in a sentence -- *"robototexnika oxumaq
    istəyirəm, DİM balım 520, IELTS 7"* -- before calling `assess_student_routes`. It reads
    only what the words support and quotes the words each value came from, so you can read
    your understanding back to the student before acting on it.

    It reports rather than resolves: a score given twice with two values comes back in
    `conflicts` and is left unset, and a subject such as "robotics" is never converted into a
    DİM field group. When `ready_to_assess` is false, ask for `still_needed` instead of
    filling it in.

    Args:
        message: what the student wrote, in Azerbaijani or English, verbatim.

    Returns:
        `fields` for the route tools, `heard` with the quote behind each value,
        `conflicts`, `still_needed`, `worth_asking`, and `interest` as plain text.
    """
    return intake_as_dict(parse_intake(message))


intake_tools: List[Any] = [read_student_message]
