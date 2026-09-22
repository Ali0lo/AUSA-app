"""The hand-curated document legalisation and recognition library.

PROVENANCE. Every step below was read from a primary page on 2026-09-16 and is
`claude-extracted`. None is `human-verified` -- that requires a named person to open the
citation (tracks/README rule 5), and the admin review queue stamps it, not this file.

COVERAGE, AND WHY IT STOPS WHERE IT DOES. Germany and Turkey are curated; the nine routes
into Poland, the USA, the UK and China are recorded as `not_collected`. That follows the
cut order in PROJECT-STATE §7 and the rule that a named absence beats a plausible guess.
Filling a country later is a data-only change to this file.

WHAT WE COULD NOT REACH, recorded rather than worked around. On 2026-09-16
`scripts.check_sources_robots` returned:

    denklik.meb.gov.tr    REFUSED -- robots.txt unreadable, DNS did not resolve
    mfa.gov.az            REFUSED -- robots.txt unreadable, SSL certificate verify failed
    studyinturkiye.gov.tr deep paths returned HTTP 418 to an automated client

So the Turkish *denklik* (equivalence) certificate and the Azerbaijani apostille procedure
are NOT written as steps here. Both are widely described by secondary sources; neither is
established by a page this project has read. They appear in `known_gaps`, which shows the
student that something is missing without telling them a requirement we cannot cite.

NOTICE WHAT GERMANY DOES *NOT* REQUIRE. uni-assist's own document pages make no mention of
an apostille or of an APS certificate for Azerbaijani applicants. That absence is recorded
deliberately: adding an apostille step "to be safe" would send a student to pay for a
legalisation no page we read asks for.
"""

from app.domain.process import (
    STATUS_CURATED,
    STATUS_NOT_COLLECTED,
    WHEN_AFTER_OFFER,
    WHEN_BEFORE_APPLYING,
    ProcessStep,
    RouteProcess,
)

READ_ON = "2026-09-16"
EXTRACTED = "claude-extracted"

UA_TRANSLATIONS = (
    "https://www.uni-assist.de/en/how-to-apply/assemble-your-documents/translations/ -- "
    "translations must be made by 'persons or institutions authorised to make translations "
    "under oath or admissible in court'; uni-assist does 'not accept non-certified "
    "translations from standard translation agencies'. Read 2026-09-16."
)
UA_CERTIFICATES = (
    "https://www.uni-assist.de/en/how-to-apply/assemble-your-documents/educational-certificates/"
    " -- 'official certificates are those bearing a signature and stamp from the issuing "
    "institution, a reference to their automatic issuance or a verification code'; upload "
    "certificates 'in their original language, accompanied by a certified translation in "
    "German or English'. Read 2026-09-16."
)
UA_TRANSCRIPT = (
    "https://www.uni-assist.de/en/how-to-apply/assemble-your-documents/educational-certificates/"
    " -- applicants with prior university study must submit 'a complete overview of all "
    "subjects and grades (transcript)'. Read 2026-09-16."
)
UA_VPD = (
    "https://www.uni-assist.de/en/how-to-apply/plan-your-application/vpd/ -- the VPD is 'a "
    "certificate issued by uni-assist which you submit directly to the university when you "
    "apply there'; processing 'usually takes 4 to 6 weeks after you have submitted your "
    "online application form' and it is valid for one year from its issue date. "
    "Read 2026-09-16."
)
STUDY_IN_TURKIYE_VISA = (
    "https://www.studyinturkiye.gov.tr/ -- 'Before coming to study in Türkiye, you need to "
    "get a student visa from the nearest Consulate of the Republic of Türkiye. Student visa "
    "procedures can take time and therefore it is important that you apply for a student "
    "visa as soon as you are admitted.' Read 2026-09-16."
)

# --- Germany: the steps every German route shares ----------------------------------------

DE_OFFICIAL_COPIES = ProcessStep(
    key="de-official-copies",
    title="Get official copies of every certificate",
    detail=(
        "A copy counts as official only if it carries the issuing institution's signature "
        "and stamp, a reference to its automatic issuance, or a verification code. Partial "
        "documents are rejected: supplementary and reverse pages are part of the certificate."
    ),
    when=WHEN_BEFORE_APPLYING,
    authority="The school or university that issued the document",
    citation=UA_CERTIFICATES, provenance=EXTRACTED, last_checked=READ_ON,
)

DE_SWORN_TRANSLATION = ProcessStep(
    key="de-sworn-translation",
    title="Have every document translated by a sworn translator",
    detail=(
        "Azerbaijani-language certificates need a translation into German or English made "
        "by a translator authorised to translate under oath or admissible in court, or by "
        "the issuing institution itself. An ordinary translation agency is not accepted. "
        "Upload the original-language document alongside the translation, never instead of it."
    ),
    when=WHEN_BEFORE_APPLYING,
    authority="A sworn (court-authorised) translator",
    citation=UA_TRANSLATIONS, provenance=EXTRACTED, last_checked=READ_ON,
)

DE_VPD = ProcessStep(
    key="de-vpd",
    title="Apply for the uni-assist VPD, and start early",
    detail=(
        "Where the university asks for one, uni-assist issues a Vorprüfungsdokumentation "
        "(VPD) that converts your grades to the German scale. It usually takes 4 to 6 weeks "
        "to process, and it is valid for one year from issue, so it can be obtained before "
        "you have chosen a final programme. You submit it to the university yourself, with "
        "the rest of your application, before that university's own deadline."
    ),
    when=WHEN_BEFORE_APPLYING,
    authority="uni-assist e.V.",
    citation=UA_VPD, provenance=EXTRACTED, last_checked=READ_ON,
)

DE_TRANSCRIPT = ProcessStep(
    key="de-transcript",
    title="Obtain a full transcript of your completed university study",
    detail=(
        "Anyone who has studied at university before applying must submit a complete "
        "overview of all subjects and grades. For the Azerbaijani preparatory year this is "
        "the document that carries the whole route: it is the evidence that the year was "
        "completed, and it needs the same sworn translation as the attestat."
    ),
    when=WHEN_BEFORE_APPLYING,
    authority="The Azerbaijani university that taught the year",
    citation=UA_TRANSCRIPT, provenance=EXTRACTED, last_checked=READ_ON,
)

DE_SCHOOL_CERTIFICATE = ProcessStep(
    key="de-school-certificate",
    title="Submit the certificate that admits you to university at home",
    detail=(
        "For a school-leaver this is the attestat. uni-assist asks for the certificate that "
        "entitles you to start university studies in your own country, which is why the "
        "attestat still has to be submitted on a route that does not accept it on its own."
    ),
    when=WHEN_BEFORE_APPLYING,
    authority="Your secondary school",
    citation=UA_CERTIFICATES, provenance=EXTRACTED, last_checked=READ_ON,
)

# The apostille is deliberately absent. See the module docstring: no page we could read
# states one for Azerbaijani applicants to Germany, and mfa.gov.az refused an automated
# check, so we can neither confirm nor cite it.
DE_GAPS = (
    "Whether an apostille is required on the attestat is not established: no uni-assist "
    "document page states one, and the Azerbaijani foreign ministry's page could not be "
    "checked (SSL verification failed on 2026-09-16). Ask the university before paying for "
    "a legalisation.",
    "Whether the destination university requires a VPD at all varies by institution and is "
    "not recorded per programme in our catalogue.",
)

DE_SHARED = (DE_OFFICIAL_COPIES, DE_SWORN_TRANSLATION, DE_VPD)

# --- Turkey -------------------------------------------------------------------------------

TR_STUDENT_VISA = ProcessStep(
    key="tr-student-visa",
    title="Apply for the student visa as soon as you are admitted",
    detail=(
        "The student visa is issued by the nearest Consulate of the Republic of Türkiye, "
        "not by the university. The published advice is to start as soon as the admission "
        "arrives, because the procedure can take time."
    ),
    when=WHEN_AFTER_OFFER,
    authority="Consulate of the Republic of Türkiye",
    citation=STUDY_IN_TURKIYE_VISA, provenance=EXTRACTED, last_checked=READ_ON,
)

TR_GAPS = (
    "The denklik (equivalence) certificate for a foreign secondary diploma is not recorded "
    "here. denklik.meb.gov.tr did not resolve on 2026-09-16, so no primary page could be "
    "read, and this project does not state a requirement it cannot cite. Assume the step "
    "may exist and ask the university.",
    "Translation and notarisation rules for Turkish applications are not established by any "
    "page we have read.",
)

_TR_NOTE = (
    "One verified step. Türkiye's document-equivalence procedure could not be reached and "
    "is listed under the gaps rather than guessed at."
)

# --- The library ---------------------------------------------------------------------------

ALL_ROUTE_PROCESSES: tuple[RouteProcess, ...] = (
    RouteProcess(
        route_key="az-prep-year",
        status=STATUS_CURATED,
        steps=(DE_TRANSCRIPT,),
        note=(
            "The preparatory year is studied in Azerbaijan, so nothing needs legalising to "
            "begin it. What matters is the document it produces: the transcript that the "
            "German and UK routes then read."
        ),
        known_gaps=(
            "Whether a UK university requires the transcript in a particular form is not "
            "recorded; only the German requirement has been read from a primary page.",
        ),
    ),
    RouteProcess(
        route_key="de-bachelor-studienkolleg",
        status=STATUS_CURATED,
        steps=DE_SHARED + (DE_SCHOOL_CERTIFICATE,),
        note=(
            "The attestat route. You submit the school certificate itself; there is no "
            "university transcript yet, which is what separates this from the prep-year route."
        ),
        known_gaps=DE_GAPS + (
            "Studienkolleg places and the Feststellungsprüfung are administered by the "
            "individual Studienkolleg; no application procedure for one has been read.",
        ),
    ),
    RouteProcess(
        route_key="de-bachelor-direct",
        status=STATUS_CURATED,
        steps=DE_SHARED + (DE_SCHOOL_CERTIFICATE, DE_TRANSCRIPT),
        note=(
            "The prep-year route into Germany. It carries the same certified-translation and "
            "VPD steps as the Studienkolleg route, plus the transcript of the completed "
            "Azerbaijani university year -- the document that makes this route work at all."
        ),
        known_gaps=DE_GAPS,
    ),
    RouteProcess(
        route_key="de-master-direct",
        status=STATUS_CURATED,
        steps=DE_SHARED + (DE_TRANSCRIPT,),
        note=(
            "A completed bachelor's degree plus its full transcript. The school certificate "
            "is not the entry document at this level."
        ),
        known_gaps=DE_GAPS,
    ),
    RouteProcess(
        route_key="tr-bachelor-direct", status=STATUS_CURATED,
        steps=(TR_STUDENT_VISA,), note=_TR_NOTE, known_gaps=TR_GAPS,
    ),
    RouteProcess(
        route_key="tr-bachelor-yos", status=STATUS_CURATED,
        steps=(TR_STUDENT_VISA,), note=_TR_NOTE, known_gaps=TR_GAPS,
    ),
    RouteProcess(
        route_key="tr-master-direct", status=STATUS_CURATED,
        steps=(TR_STUDENT_VISA,), note=_TR_NOTE, known_gaps=TR_GAPS,
    ),
) + tuple(
    RouteProcess(
        route_key=key,
        status=STATUS_NOT_COLLECTED,
        steps=(),
        note=(
            "Nobody has curated the document procedure for this route. This is a gap in our "
            "catalogue, not a finding that the route needs no paperwork -- assume documents "
            "must be translated and certified, and ask the university what it requires."
        ),
    )
    for key in (
        "uk-bachelor-direct", "uk-bachelor-foundation", "uk-master-direct",
        "us-bachelor-direct", "us-master-direct",
        "pl-bachelor-direct", "pl-master-direct",
        "cn-bachelor-csc", "cn-master-direct",
    )
)

PROCESS_BY_ROUTE_KEY: dict[str, RouteProcess] = {p.route_key: p for p in ALL_ROUTE_PROCESSES}
