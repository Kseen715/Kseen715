#!/usr/bin/env python3
"""Reflow github-readme-stats compact top-langs SVG: pack language
entries greedily into rows by width, wrapping like words in a paragraph.
Short names => more per row; long names => fewer."""
import re, sys, os

ROW_HEIGHT = float(os.environ.get("ROW_HEIGHT", 15))
PADDING_X = float(os.environ.get("PADDING_X", 25))
GAP = float(os.environ.get("GAP", 5))          # space between entries
CHAR_W = float(os.environ.get("CHAR_W", 6.2))   # px per char at 11px font
DOT_W = float(os.environ.get("DOT_W", 15))      # circle + gap before text
MAX_WIDTH_ENV = os.environ.get("MAX_WIDTH")


def label_of(entry: str) -> str:
    m = re.search(r'<text[^>]*class=.lang-name.[^>]*>(.*?)</text>',
                  entry, re.DOTALL)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ""


def entry_width(entry: str) -> float:
    return DOT_W + len(label_of(entry)) * CHAR_W


def reflow(svg: str) -> str:
    items_match = re.search(
        r'(<svg\s+data-testid="lang-items"[^>]*>)(.*?)(</svg>)', svg, re.DOTALL)
    if not items_match:
        sys.stderr.write("lang-items block not found; untouched\n")
        return svg
    open_tag, body, close_tag = items_match.groups()

    card_width = None
    m = re.search(r'<svg[^>]*\bwidth="(\d+(?:\.\d+)?)"', svg)
    if m:
        card_width = float(m.group(1))
    if card_width is None:
        m = re.search(r'viewBox="0 0 (\d+(?:\.\d+)?)', svg)
        if m:
            card_width = float(m.group(1))
    if card_width is None:
        card_width = 500.0
    max_width = float(MAX_WIDTH_ENV) if MAX_WIDTH_ENV else card_width - 2 * PADDING_X

    entries = re.findall(r'<g\s+class="stagger".*?</g>\s*', body, re.DOTALL)
    if not entries:
        sys.stderr.write("no language entries; untouched\n")
        return svg

    wrapper_match = re.search(
        r'<g\s+transform="translate\(0,\s*25\)">\s*<g\s+transform="translate\(', body)
    if wrapper_match:
        prefix = body[:wrapper_match.start()]
    else:
        first = body.find('<g class="stagger"')
        gpos = body.rfind('<g transform="translate(', 0, first)
        prefix = body[:gpos] if gpos != -1 else body[:first]

    laid = []
    x = 0.0
    rows = 0
    for entry in entries:
        w = entry_width(entry)
        if x > 0 and x + w > max_width:
            rows += 1
            x = 0.0
        y = rows * ROW_HEIGHT
        laid.append(f'<g transform="translate({x:g}, {y:g})">{entry.strip()}</g>')
        x += w + GAP
    n_rows = rows + 1

    grid = '<g transform="translate(0, 25)">' + "".join(laid) + '</g>'
    new_items = open_tag + prefix + grid + "\n      " + close_tag
    svg = svg[:items_match.start()] + new_items + svg[items_match.end():]

    new_height = int(55 + 25 + n_rows * ROW_HEIGHT + 10)
    svg = re.sub(r'(<svg[^>]*\bheight=")\d+(?:\.\d+)?(")',
                 rf'\g<1>{new_height}\g<2>', svg, count=1)
    svg = re.sub(r'(viewBox="0 0 \d+(?:\.\d+)? )\d+(?:\.\d+)?(")',
                 rf'\g<1>{new_height}\g<2>', svg, count=1)
    return svg


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: reflow_langs.py <in.svg> [out.svg]\n")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else inp
    with open(inp, encoding="utf-8") as f:
        svg = f.read()
    with open(out, "w", encoding="utf-8") as f:
        f.write(reflow(svg))


if __name__ == "__main__":
    main()
