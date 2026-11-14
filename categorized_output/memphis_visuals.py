"""Shared data loading and chart rendering for Memphis_Flock_Analysis.ipynb."""

import csv
import re
from collections import Counter
from html import escape
from pathlib import Path
from IPython.display import HTML, SVG, display

def load_data(path=None):
    """Load a fresh copy of the Memphis records for an independent chart cell."""
    path = Path(path) if path is not None else Path(__file__).with_name("Memphis_categorized_clean.csv")
    with path.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError("The dataset contains no rows.")
    return rows


def percent_chart(counts, title, denominator=None):
    """Display a horizontal percentage chart and an exact count table."""
    denominator = sum(counts.values()) if denominator is None else denominator
    if denominator <= 0:
        raise ValueError("A positive denominator is required.")
    width, left, plot_width, top, step = 1050, 320, 550, 85, 42
    height = top + step * len(counts) + 45
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="{escape(title, quote=True)}" '
             'style="max-width:1050px;width:100%;background:white;font-family:Arial,sans-serif">',
             f'<text x="20" y="28" font-size="20" fill="#182235">{escape(title)}</text>',
             f'<text x="20" y="50" font-size="13" fill="#526075">Denominator: {denominator:,} records</text>']
    for tick in range(0, 101, 20):
        x = left + plot_width * tick / 100
        parts.append(f'<line x1="{x}" y1="{top-10}" x2="{x}" y2="{height-35}" stroke="#e5eaf0"/>')
        parts.append(f'<text x="{x}" y="{height-12}" text-anchor="middle" font-size="12" fill="#526075">{tick}%</text>')
    table_rows = []
    for index, (label, count) in enumerate(counts.items()):
        percent = 100 * count / denominator
        y = top + index * step
        parts.append(f'<text x="{left-12}" y="{y+19}" text-anchor="end" font-size="14" fill="#182235">{escape(str(label))}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{plot_width * percent / 100:.2f}" height="27" rx="4" fill="#2879b9"/>')
        parts.append(f'<text x="{left+plot_width+12}" y="{y+19}" font-size="14" fill="#182235">{percent:.2f}% ({count:,})</text>')
        table_rows.append(f'<tr><td>{escape(str(label))}</td><td>{count:,}</td><td>{percent:.2f}%</td></tr>')
    parts.append('</svg>')
    display(SVG(''.join(parts)))
    display(HTML('<table><thead><tr><th>Group</th><th>Records</th><th>Percent</th></tr></thead>'
                 '<tbody>' + ''.join(table_rows) + '</tbody></table>'))

