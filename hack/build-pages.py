#!/usr/bin/env python3
"""Build the GitHub Pages site from docs/.

Rules:
- Copy docs/ to _site/ unchanged so original Markdown remains downloadable.
- For every Markdown file under docs/, generate a sibling .html in _site/.
- If docs/ already contains a hand-written HTML file with the same relative path,
  keep that HTML and do not overwrite it.
"""

from __future__ import annotations

import html
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = ROOT / "_site"


def extract_title(source: str, fallback: str) -> str:
    for line in source.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def render_page(title: str, body: str, md_href: str) -> str:
    safe_title = html.escape(title)
    safe_md_href = html.escape(md_href, quote=True)
    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>{safe_title}</title>
<style>
  :root {{
    --bg: #f6f7f9;
    --panel: #ffffff;
    --text: #1f2328;
    --muted: #656d76;
    --border: #d8dee4;
    --blue: #0969da;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", \"Microsoft YaHei\", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.75;
  }}
  .page {{
    width: min(920px, calc(100% - 32px));
    margin: 0 auto;
    padding: 36px 0 64px;
  }}
  .toolbar {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 18px;
    font-size: 14px;
  }}
  .toolbar a {{ color: var(--blue); text-decoration: none; }}
  article {{
    padding: 34px 40px;
    border: 1px solid var(--border);
    border-radius: 16px;
    background: var(--panel);
  }}
  h1, h2, h3 {{ line-height: 1.3; }}
  h1 {{ margin-top: 0; }}
  h2 {{ margin-top: 32px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }}
  code {{
    padding: .15em .35em;
    border-radius: 6px;
    background: #eff1f3;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }}
  pre {{
    overflow-x: auto;
    padding: 18px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: #f6f8fa;
  }}
  pre code {{ padding: 0; background: transparent; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 8px 10px; border: 1px solid var(--border); text-align: left; }}
  blockquote {{ margin-left: 0; padding-left: 16px; border-left: 4px solid var(--border); color: var(--muted); }}
  @media (max-width: 640px) {{ article {{ padding: 24px 20px; }} }}
</style>
</head>
<body>
<main class=\"page\">
  <nav class=\"toolbar\">
    <a href=\"/kubernetes/\">← 返回文档首页</a>
    <a href=\"{safe_md_href}\" download>下载 Markdown</a>
  </nav>
  <article>
{body}
  </article>
</main>
</body>
</html>
"""


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(DOCS, SITE)

    generated = 0
    skipped = 0

    for md_path in DOCS.rglob("*.md"):
        rel = md_path.relative_to(DOCS)
        source_html = DOCS / rel.with_suffix(".html")
        output_html = SITE / rel.with_suffix(".html")

        if source_html.exists():
            skipped += 1
            continue

        source = md_path.read_text(encoding="utf-8")
        title = extract_title(source, md_path.stem.replace("-", " ").title())
        body = markdown.markdown(
            source,
            extensions=["fenced_code", "tables", "sane_lists"],
            output_format="html5",
        )
        md_href = md_path.name
        output_html.parent.mkdir(parents=True, exist_ok=True)
        output_html.write_text(render_page(title, body, md_href), encoding="utf-8")
        generated += 1

    print(f"Pages build complete: generated={generated}, preserved_html={skipped}, output={SITE}")


if __name__ == "__main__":
    main()
