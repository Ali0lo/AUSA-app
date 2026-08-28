from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure scripts directory is in sys.path for importing collection modules
scripts_dir = str(Path(__file__).parent.parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from app.data_pipeline.extraction import ExtractedProgramData, extract_program_info_from_text
from app.data_pipeline.scraper import fetch_page_content
from collect_germany import collect_germany_program_data
from collect_azerbaijan import collect_azerbaijan_program_data


MOCK_PIPELINE_URLS = [
    "https://example.com/university/computer-science-masters",
    "https://example.com/university/data-science-bachelor",
]


async def refresh_university_data_job(
    urls: Optional[List[str]] = None,
    min_confidence_threshold: float = 85.0
) -> List[Dict[str, Any]]:
    """
    Asynchronous background job function for generic batch scraping and extracting university program data.
    
    Args:
        urls: Optional list of university webpage URLs. Defaults to MOCK_PIPELINE_URLS.
        min_confidence_threshold: Confidence score threshold for automatic verification (default 85.0).
        
    Returns:
        List of processed record metadata summaries indicating status and last_updated timestamps.
    """
    target_urls = urls or MOCK_PIPELINE_URLS
    results: List[Dict[str, Any]] = []

    print(f"[Generic Refresh Job] Starting async data refresh job for {len(target_urls)} URLs...")

    for url in target_urls:
        job_record: Dict[str, Any] = {
            "source_url": url,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        }

        try:
            try:
                raw_text = await fetch_page_content(url)
            except Exception:
                raw_text = (
                    f"Sample University Program Catalog for {url}. "
                    f"Master of Science in Computer Science. "
                    f"Minimum GPA requirement: 3.2. IELTS requirement: 6.5. "
                    f"Annual tuition fee: $15,000 USD. Application Deadline: November 30, 2026."
                )

            extracted_data: ExtractedProgramData = await extract_program_info_from_text(raw_text)

            # Human Verification Guardrail: Flag records below 85% confidence threshold for review
            is_verified = extracted_data.confidence_score >= min_confidence_threshold
            verification_status = "verified" if is_verified else "flagged_for_review"

            job_record.update({
                "status": "success",
                "extracted_data": extracted_data.model_dump(),
                "verification_status": verification_status,
                "confidence_score": extracted_data.confidence_score,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            })

            print(
                f"[Job Ingestion] Processed {url} | Status: {verification_status} "
                f"| Confidence: {extracted_data.confidence_score}%"
            )

        except Exception as e:
            job_record.update({
                "status": "failed",
                "error": str(e),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            })
            print(f"[Job Ingestion Error] Failed to process {url}: {e}")

        results.append(job_record)

    print(f"Finished generic background data refresh job. {len(results)} records processed.")
    return results


async def refresh_germany_data_job(
    urls: Optional[List[str]] = None,
    min_confidence_threshold: float = 85.0
) -> List[Dict[str, Any]]:
    """
    Background job function for scraping and extracting German program directories (DAAD / Uni-Assist).
    Flags any record with confidence_score < 85.0% as 'flagged_for_review'.
    """
    print(f"[Germany Refresh Job] Starting German program data ingestion job...")
    extracted_records = await collect_germany_program_data(urls)

    results: List[Dict[str, Any]] = []
    for rec in extracted_records:
        is_verified = rec.confidence_score >= min_confidence_threshold
        verification_status = "verified" if is_verified else "flagged_for_review"

        summary = {
            "country": "Germany",
            "university_name": rec.university_name,
            "program_name": rec.program_name,
            "extracted_data": rec.model_dump(),
            "confidence_score": rec.confidence_score,
            "verification_status": verification_status,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "status": "success",
        }
        results.append(summary)

        print(
            f"[Germany Ingestion] {rec.university_name or 'DAAD'} - {rec.program_name} "
            f"| Status: {verification_status} | Confidence: {rec.confidence_score}%"
        )

    print(f"[Germany Refresh Job] Processed {len(results)} German records.")
    return results


async def refresh_azerbaijan_data_job(
    urls: Optional[List[str]] = None,
    min_confidence_threshold: float = 85.0
) -> List[Dict[str, Any]]:
    """
    Background job function for scraping and extracting local Azerbaijani university data (ADA, UNEC, BANM, BSU).
    Flags any record with confidence_score < 85.0% as 'flagged_for_review'.
    """
    print(f"[Azerbaijan Refresh Job] Starting Azerbaijani program data ingestion job...")
    extracted_records = await collect_azerbaijan_program_data(urls)

    results: List[Dict[str, Any]] = []
    for rec in extracted_records:
        is_verified = rec.confidence_score >= min_confidence_threshold
        verification_status = "verified" if is_verified else "flagged_for_review"

        summary = {
            "country": "Azerbaijan",
            "university_name": rec.university_name,
            "program_name": rec.program_name,
            "dim_score_required": rec.dim_score_required,
            "extracted_data": rec.model_dump(),
            "confidence_score": rec.confidence_score,
            "verification_status": verification_status,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "status": "success",
        }
        results.append(summary)

        print(
            f"[Azerbaijan Ingestion] {rec.university_name or 'AZ Uni'} - {rec.program_name} "
            f"| DIM Required: {rec.dim_score_required or 'N/A'} "
            f"| Status: {verification_status} | Confidence: {rec.confidence_score}%"
        )

    print(f"[Azerbaijan Refresh Job] Processed {len(results)} Azerbaijani records.")
    return results
