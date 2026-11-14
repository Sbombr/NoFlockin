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


def percent_chart(counts, title, denominator=None, interpretation=None):
    """Show percentages with the mean across displayed groups and all extrema."""
    if not counts:
        return
    denominator = sum(counts.values()) if denominator is None else denominator
    if denominator <= 0:
        raise ValueError("A positive denominator is required.")
    average = sum(counts.values()) / len(counts)
    lowest, highest = min(counts.values()), max(counts.values())
    width, left, plot_width, top, step = 1200, 320, 550, 110, 42
    height = top + step * len(counts) + 60
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="{escape(title, quote=True)}" style="max-width:1200px;width:100%;background:white;font-family:Arial,sans-serif">',
             f'<text x="20" y="28" font-size="19" fill="#182235">{escape(title)}</text>',
             f'<text x="20" y="51" font-size="13" fill="#526075">Denominator: {denominator:,} records</text>',
             f'<text x="20" y="75" font-size="13">Average across displayed groups: {average:,.1f} ({100*average/denominator:.2f}%) · Lowest: {lowest:,} · Highest: {highest:,}</text>']
    for tick in range(0, 101, 20):
        x = left + plot_width * tick / 100
        parts.append(f'<line x1="{x}" y1="{top-10}" x2="{x}" y2="{height-45}" stroke="#e5eaf0"/>')
        parts.append(f'<text x="{x}" y="{height-22}" text-anchor="middle" font-size="12" fill="#526075">{tick}%</text>')
    table_rows = []
    for index, (label, count) in enumerate(counts.items()):
        percent = 100 * count / denominator
        y = top + index * step
        tags = [tag for tag, value in [('Lowest', lowest), ('Highest', highest)] if count == value]
        color = '#eb6834' if count == highest else '#1baf7a' if count == lowest else '#2879b9'
        suffix = ' — ' + ' / '.join(tags) if tags else ''
        parts.append(f'<text x="{left-12}" y="{y+19}" text-anchor="end" font-size="14" fill="#182235">{escape(str(label))}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{plot_width * percent / 100:.2f}" height="27" rx="4" fill="{color}"/>')
        parts.append(f'<text x="{left+plot_width+12}" y="{y+19}" font-size="13" fill="#182235">{percent:.2f}% ({count:,}){suffix}</text>')
        table_rows.append(f'<tr><td>{escape(str(label))}</td><td>{count:,}</td><td>{percent:.2f}%</td></tr>')
    avg_x = left + plot_width * average / denominator
    parts.append(f'<line x1="{avg_x}" x2="{avg_x}" y1="{top-10}" y2="{height-45}" stroke="#182235" stroke-width="2" stroke-dasharray="5 4"><title>Average across displayed groups: {average:,.1f} records ({100*average/denominator:.2f}%)</title></line>')
    parts.append('</svg>')
    display(SVG(''.join(parts)))
    if interpretation:
        display(HTML(f'<p><em>Possible explanation:</em> {escape(interpretation)}</p>'))
    display(HTML('<table><thead><tr><th>Group</th><th>Records</th><th>Percent</th></tr></thead>'
                 '<tbody>' + ''.join(table_rows) + '</tbody></table>'))


def series_chart(series, title, percent=False, interpretation=None):
    """Mark each series' average and all lowest/highest unmasked observations."""
    import math
    labels = sorted(set().union(*(set(s) for s in series.values())))
    width, left, top, pw, ph = 1200, 70, 55, 1060, 215
    height = 340 + 48 * len(series)
    values = [v for s in series.values() for v in s.values() if v is not None and math.isfinite(v)]
    ymax = 100 if percent else max(values + [1]) * 1.1
    def fmt(value): return f'{value:,.2f}%' if percent else f'{value:,.1f}'
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title, quote=True)}" style="width:100%;max-width:1200px;background:white;font-family:Arial">', f'<text x="15" y="23" font-size="17">{escape(title)}</text>']
    for i in range(5):
        y = top + ph * (1-i/4)
        parts += [f'<line x1="{left}" x2="{left+pw}" y1="{y}" y2="{y}" stroke="#e4e3df"/>', f'<text x="{left-8}" y="{y+4}" text-anchor="end" font-size="11">{ymax*i/4:.0f}{"%" if percent else ""}</text>']
    for j,(name,s) in enumerate(series.items()):
        color = ['#2a78d6','#eb6834','#1baf7a','#eda100'][j%4]
        observations = [(i,label,s.get(label)) for i,label in enumerate(labels) if s.get(label) is not None and math.isfinite(s[label])]
        if not observations: continue
        vals = [v for _,_,v in observations]
        avg, low, high = sum(vals)/len(vals), min(vals), max(vals)
        avg_y = top + ph*(1-avg/ymax)
        parts.append(f'<line x1="{left}" x2="{left+pw}" y1="{avg_y}" y2="{avg_y}" stroke="{color}" stroke-dasharray="6 4" opacity="0.65"><title>{escape(name)} average: {fmt(avg)}</title></line>')
        points=[]
        for i,label in enumerate(labels):
            value=s.get(label)
            if value is None or not math.isfinite(value):
                if points: parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"/>')
                points=[]
                continue
            x=left+pw*i/max(1,len(labels)-1); y=top+ph*(1-value/ymax)
            points.append(f'{x},{y}')
            parts.append(f'<circle cx="{x}" cy="{y}" r="2.4" fill="{color}"><title>{escape(str(label))}: {fmt(value)}</title></circle>')
            if value == low:
                parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="white" stroke="{color}" stroke-width="2"><title>Lowest: {escape(str(label))}, {fmt(value)}</title></circle>')
            if value == high:
                parts.append(f'<rect x="{x-4}" y="{y-4}" width="8" height="8" fill="{color}" stroke="white"><title>Highest: {escape(str(label))}, {fmt(value)}</title></rect>')
        if points: parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"/>')
        def where(value):
            matches=[str(label) for _,label,v in observations if v==value]
            return ', '.join(matches[:2]) + (f' (+{len(matches)-2} ties)' if len(matches)>2 else '')
        parts.append(f'<text x="{left}" y="{329+j*48}" fill="{color}" font-size="13">{escape(name)} — Average: {fmt(avg)} (dashed line)</text>')
        parts.append(f'<text x="{left}" y="{348+j*48}" fill="{color}" font-size="12">○ Lowest: {fmt(low)} at {escape(where(low))} · ■ Highest: {fmt(high)} at {escape(where(high))}</text>')
    for i,label in enumerate(labels):
        if i%max(1,len(labels)//9)==0 or i==len(labels)-1:
            parts.append(f'<text x="{left+pw*i/max(1,len(labels)-1)}" y="295" text-anchor="middle" font-size="10">{escape(str(label))}</text>')
    parts.append(f'<text x="{left}" y="{height-10}" font-size="11" fill="#526075">Averages use plotted observations only; masked values are excluded. All tied extrema are marked.</text>')
    display(SVG(''.join(parts)+'</svg>'))
    if interpretation:
        display(HTML(f'<p><em>Possible explanation:</em> {escape(interpretation)}</p>'))


def load_analysis_data(path=None):
    """Load Memphis audit rows and conservatively merge candidate copies."""
    import json
    from collections import defaultdict
    from datetime import datetime
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("America/Chicago")
    path = path if path is not None else Path(__file__).resolve().parents[1] / "new_normalizations/Memphis_categorized.csv"
    def parse_time(value):
        try: return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(LOCAL_TZ)
        except (ValueError, AttributeError): return None

    def source_files(row):
        try: return {s.get('filename') or s.get('source_url', '(unnamed)') for s in json.loads(row['sources'] or '[]')}
        except (ValueError, TypeError): return set()

    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        raw = list(csv.DictReader(f))
    valid = [r for r in raw if parse_time(r['search_time_utc'])]
    invalid = [r for r in raw if not parse_time(r['search_time_utc'])]
    KEY = ['search_time_utc', 'start_timeframe_utc', 'end_timeframe_utc', 'search_type']
    groups = defaultdict(list)
    for r in valid: groups[tuple(r[k] for k in KEY)].append(r)
    records, conflicts = [], []
    for key, copies in groups.items():
        reasons = {re.sub(r'\s+', ' ', r['reason'].strip().casefold()) for r in copies if r['reason'].strip()}
        if len(reasons) > 1:
            conflicts.append((key, copies))
            partitions = [[r] for r in copies]  # preserve every row when reason texts conflict
        else:
            partitions = [copies]
        for partition in partitions:
            ranked = sorted(partition, key=lambda r: (bool(r['reason'].strip()), sum(bool(v.strip()) for v in r.values())), reverse=True)
            row = {k: next((r[k] for r in ranked if r[k].strip()), '') for k in valid[0]}
            row['_sources'] = set().union(*(source_files(r) for r in partition))
            row['_copies'] = len(partition)
            row['_time'] = parse_time(row['search_time_utc'])
            row['_month'] = row['_time'].strftime('%Y-%m')
            row['_reason'] = re.sub(r'\s+', ' ', row['reason'].upper().replace('+', ' ')).strip()
            row['_category'] = row['reason_category'] if row['reason'].strip() else 'Reason not recorded'
            records.append(row)
    records.sort(key=lambda r: r['_time'])

    return raw, valid, invalid, records, conflicts


def percent_chart_plain(counts, title, denominator=None, interpretation=None):
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
    if interpretation:
        display(HTML(f'<p><em>Possible explanation:</em> {escape(interpretation)}</p>'))
    display(HTML('<table><thead><tr><th>Group</th><th>Records</th><th>Percent</th></tr></thead>'
                 '<tbody>' + ''.join(table_rows) + '</tbody></table>'))

def series_chart_plain(series, title, percent=False, interpretation=None):
    labels = sorted(set().union(*(set(s) for s in series.values())))
    width, height, left, top, pw, ph = 1100, 340, 70, 55, 980, 215
    values = [v for s in series.values() for v in s.values() if v is not None]
    ymax = 100 if percent else max(values + [1]) * 1.1
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" style="width:100%;max-width:1100px;background:white;font-family:Arial">', f'<text x="15" y="23" font-size="17">{escape(title)}</text>']
    for i in range(5):
        y = top + ph * (1-i/4)
        parts += [f'<line x1="{left}" x2="{left+pw}" y1="{y}" y2="{y}" stroke="#e4e3df"/>', f'<text x="{left-8}" y="{y+4}" text-anchor="end" font-size="11">{ymax*i/4:.0f}{"%" if percent else ""}</text>']
    for j,(name,s) in enumerate(series.items()):
        color = ['#2a78d6','#eb6834','#1baf7a','#eda100'][j%4]
        points=[]
        for i,label in enumerate(labels):
            value=s.get(label)
            if value is None:
                if points: parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"/>')
                points=[]
                continue
            x=left+pw*i/max(1,len(labels)-1); y=top+ph*(1-value/ymax)
            points.append(f'{x},{y}')
            parts.append(f'<circle cx="{x}" cy="{y}" r="2.4" fill="{color}"><title>{escape(str(label))}: {value:.2f}</title></circle>')
        if points: parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<text x="{left+j*245}" y="330" fill="{color}" font-size="12">{escape(name)}</text>')
    for i,label in enumerate(labels):
        if i%max(1,len(labels)//9)==0 or i==len(labels)-1:
            parts.append(f'<text x="{left+pw*i/max(1,len(labels)-1)}" y="295" text-anchor="middle" font-size="10">{escape(str(label))}</text>')
    display(SVG(''.join(parts)+'</svg>'))
    if interpretation:
        display(HTML(f'<p><em>Possible explanation:</em> {escape(interpretation)}</p>'))
