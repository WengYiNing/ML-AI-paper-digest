"""Render digest templates."""
from __future__ import annotations

from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mldigest.models import Paper


def render_digest(papers: List[Paper], context: dict, templates_dir: Path) -> tuple[str, str]:
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    html_template = env.get_template("digest.html.j2")
    text_template = env.get_template("digest.txt.j2")
    html = html_template.render(papers=papers, **context)
    text = text_template.render(papers=papers, **context)
    return html, text
