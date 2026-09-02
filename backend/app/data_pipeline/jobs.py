from datetime import datetime, timezone
from typing import Any, Dict, List

from app.data_pipeline.extraction import ExtractedProgramData, extract_program_info_from_text
from app.data_pipeline.scraper import fetch_page_content


async def refresh_university_data_job(
    urls: List[str],
    min_confidence_threshold: float = 85.0
) -> List[Dict[str, Any]]:
    """
    Asynchronous background job for batch scraping and extracting university program data.

    Args:
        urls: University webpage URLs to process. Required -- there is no default list,
            because a job with nothing real to fetch should not run at all.
        min_confidence_threshold: Below this extraction confidence, the record is marked
            needs_review. It never marks a record verified: see the provenance note below.

    Returns:
        One record per URL. A URL that could not be fetched or parsed yields
        status "failed" and no extracted_data -- never a substitute.
    """
    results: List[Dict[str, Any]] = []

    print(f"[Refresh Job] Starting async data refresh job for {len(urls)} URLs...")

    for url in urls:
        job_record: Dict[str, Any] = {
            "source_url": url,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        }

        try:
            # No fallback text. If the fetch fails, the record fails -- see the note below.
            raw_text = await fetch_page_content(url)
            extracted_data: ExtractedProgramData = await extract_program_info_from_text(raw_text)

            job_record.update({
                "status": "success",
                "extracted_data": extracted_data.model_dump(),
                # Provenance is always claude-extracted. Only a human inspecting the source
                # page can move a record to human-verified, and an LLM's own confidence score
                # is not that human. Low confidence flags the record for review sooner; it
                # never promotes one.
                "provenance": "claude-extracted",
                "needs_review": extracted_data.confidence_score < min_confidence_threshold,
                "confidence_score": extracted_data.confidence_score,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            })

            print(
                f"[Job Ingestion] Processed {url} | provenance: claude-extracted "
                f"| confidence: {extracted_data.confidence_score}%"
            )

        except Exception as e:
            job_record.update({
                "status": "failed",
                "error": str(e),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            })
            print(f"[Job Ingestion Error] Failed to process {url}: {e}")

        results.append(job_record)

    succeeded = sum(1 for r in results if r["status"] == "success")
    print(f"Finished data refresh job. {succeeded}/{len(results)} URLs processed successfully.")
    return results


# refresh_azerbaijan_data_job was REMOVED on 2026-08-29.
#
# It called collect_azerbaijan_program_data, which caught a bare Exception on any network
# failure and silently substituted hardcoded mock HTML containing invented DIM scores
# (ADA 600, UNEC 520, BHOS 650). Those fabricated scores were then marked "verified"
# whenever their confidence_score cleared 85, and written into the pipeline as real
# admission requirements. ADR-0004 forbids exactly this.
#
# Azerbaijani data now comes from backend/scripts/collect_azerbaijan.py, which builds
# program_cutoff_history from published DIM results and exits rather than guessing.
# It is a batch collector, not a request-path job, so it has no replacement here.
#
#
# refresh_germany_data_job was REMOVED on 2026-08-30, together with
# backend/scripts/collect_germany.py, for the same defect in a worse form.
#
# The collector could never return real data. Its three target URLs were invented
# (daad.de/.../detail/tu-munich-msc-informatics, uni-assist.de/en/tools/check-university-
# admission/rwth-aachen-mechanical-engineering), so every fetch 404'd; the bare
# `except Exception: pass` then fell through to MOCK_GERMAN_HTML_MAP, which carried made-up
# GPA, IELTS, tuition and deadline values for TU Munich, Heidelberg and RWTH Aachen. It also
# hardcoded blocked_account_eur = 11208.0 whenever extraction found none -- a stale figure
# presented as fact. The job then marked those records "verified" above 85% confidence, and
# test_refresh_germany_data_job asserted status == "success" for all of them, so the suite
# stayed green on entirely fabricated German admission requirements.
#
# Germany will be collected from official sources -- hochschulstart.de for NC values and
# university admissions pages for requirements -- by the requirements collector described in
# docs/adr/0007. Nothing replaces this job in the request path.
#
#
# The generic job above previously carried the same defect: a bare `except Exception` around
# fetch_page_content substituted "Sample University Program Catalog for {url}... GPA 3.2,
# IELTS 6.5, $15,000 USD, deadline November 30, 2026", extracted from that invention, and
# marked the result verified. Removed 2026-08-30. A URL that cannot be fetched now fails.
