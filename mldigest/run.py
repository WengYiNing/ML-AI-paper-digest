from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
from mldigest.config import load_config, masked_config
from mldigest.delivery.smtp_sender import send_email
from mldigest.ingest.arxiv_client import fetch_arxiv_papers
from mldigest.ingest.hf_client import fetch_hf_hits
from mldigest.ingest.openreview_client import fetch_openreview_papers
from mldigest.models import Paper
from mldigest.report.render import render_digest
from mldigest.selector.orchestrator import orchestrate_selection
from mldigest.storage.artifacts import write_artifacts
from mldigest.utils import get_logger, window_bounds

logger = get_logger(__name__)

def _apply_keyphrases(papers: list[Paper], enable: bool) -> None:
    if not enable:
        return
    import importlib.util

    if importlib.util.find_spec("yake") is None:
        return
    import importlib

    yake_module = importlib.import_module("yake")
    extractor = yake_module.KeywordExtractor(top=8)
    for paper in papers:
        if not paper.abstract:
            continue
        phrases = [phrase for phrase, _score in extractor.extract_keywords(paper.abstract)]
        paper.keyphrases = phrases

def _print_summary(papers: list[Paper]) -> None:
    for paper in papers:
        logger.info("[%s] %s", paper.signals.get("role"), paper.title)


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly ML / AI paper digest generator")
    parser.add_argument("--config", required=True, help="Path to config YAML")
    parser.add_argument("--dry-run", action="store_true", help="Skip email delivery")
    parser.add_argument("--print", dest="print_out", action="store_true", help="Print summary to stdout")
    args = parser.parse_args()

    cfg = load_config(args.config).data
    schedule = cfg["schedule"]
    window_days = int(schedule["window_days"])
    window_start, window_end = window_bounds(window_days)

    arxiv_papers: list[Paper] = []
    if cfg["sources"]["arxiv"]["enabled"]:
        arxiv_papers = fetch_arxiv_papers(
            cfg["sources"]["arxiv"]["categories"],
            start=0,
            max_results=cfg["limits"]["arxiv_max_results"],
            window_days=window_days,
        )

    hf_hits = {}
    if cfg["sources"]["hf"]["enabled"]:
        hf_hits = fetch_hf_hits(cfg["sources"]["hf"]["queries"])

    openreview_papers: list[Paper] = []
    if cfg["sources"]["openreview"]["enabled"]:
        openreview_papers = fetch_openreview_papers(
            cfg["sources"]["openreview"]["venues"],
            accept_only=cfg["sources"]["openreview"]["accept_only"],
        )

    selected, scoring_debug = orchestrate_selection(arxiv_papers, openreview_papers, hf_hits, cfg)
    _apply_keyphrases(selected, cfg["limits"]["enable_keyphrases"])

    subject = f"{cfg['email']['subject_prefix']} — {datetime.now().strftime('%Y-%m')} — {len(selected)} papers"
    context = {
        "subject": subject,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
    }
    html, text = render_digest(
        selected,
        context=context,
        templates_dir=Path(__file__).parent / "report" / "templates",
    )

    payload = {
        "config_snapshot": masked_config(cfg),
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "counts": {
            "arxiv_candidates": len(arxiv_papers),
            "openreview_candidates": len(openreview_papers),
            "hf_hits_count": len(hf_hits),
        },
        "scoring_debug": scoring_debug,
    }

    artifact_paths = write_artifacts(cfg["storage"]["runs_dir"], selected, html, text, payload)
    logger.info("Artifacts written: %s", artifact_paths)

    if args.print_out:
        _print_summary(selected)

    if cfg["email"]["enabled"] and not args.dry_run:
        send_email(
            subject=subject,
            sender_name=cfg["email"]["from_name"],
            sender_address=cfg["email"]["from_address"],
            to_addresses=cfg["email"]["to_addresses"],
            html_body=html,
            text_body=text,
            smtp_host=cfg["email"]["smtp_host"],
            smtp_port=int(cfg["email"]["smtp_port"]),
            use_tls=cfg["email"]["use_tls"],
        )
        logger.info("Email sent")


if __name__ == "__main__":
    main()
