#!/usr/bin/env python3
"""Extract KPI/duration/hourly/outcomes/transfers data and call paths from raw CSVs.

Reads raw CSV exports from CSV Files/, parses the Queue column for call path
extraction, and produces summary CSVs in Reports/Charts/ for use by
generate_report.py.

Usage:
    cd scripts
    python3 extract_html_data.py
    # or specify category:
    python3 extract_html_data.py Switchboard
"""

import os
import sys
import csv
import io
from collections import Counter, defaultdict
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(PROJECT_DIR, "CSV Files")
CHARTS_DIR = os.path.join(PROJECT_DIR, "Reports", "Charts")

MONTH_MAP = {
    'April': 'April', 'April ': 'April',
    'May': 'May', 'May ': 'May',
    'June': 'June', 'June ': 'June',
    'July': 'July', 'Jul': 'July',
    'August': 'August', 'Aug': 'August',
    'September': 'September', 'Sep': 'September',
    'October': 'October', 'Oct': 'October',
    'November': 'November', 'Nov': 'November',
    'December': 'December', 'Dec': 'December',
    'January': 'January', 'Jan': 'January',
    'February': 'February', 'Feb': 'February',
    'March': 'March', 'Mar': 'March',
}

MONTH_ORDER = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']


def parse_month_sort_key(month_name):
    """Return sort key for month name (lower case comparison)."""
    for i, m in enumerate(MONTH_ORDER):
        if month_name.lower() == m.lower():
            return i
    return 99


def detect_category(filename):
    """Extract category from filename. Handles both separators:
    - 'doc_xxx_Switchboard-April.csv' -> 'Switchboard'
    - 'doc_xxx_Non-ATTY June.csv' -> 'Non-ATTY'
    - 'doc_xxx_LRS Spanish April.csv' -> 'LRS Spanish'
    """
    base = os.path.splitext(os.path.basename(filename))[0]
    parts = base.split('_')
    if len(parts) < 2:
        return 'Unknown'

    last_part = parts[-1]

    # Try space split first (handles 'Non-ATTY June', 'LRS Spanish April')
    space_split = last_part.rsplit(' ', 1)
    if len(space_split) >= 2:
        potential_month = space_split[-1].strip()
        potential_category = space_split[0].strip()
        for k, v in MONTH_MAP.items():
            if k.lower() in potential_month.lower():
                return potential_category

    # Try hyphen split (handles 'Switchboard-April')
    hyphen_split = last_part.rsplit('-', 1)
    if len(hyphen_split) >= 2:
        potential_month = hyphen_split[-1].strip()
        potential_category = hyphen_split[0].strip()
        for k, v in MONTH_MAP.items():
            if k.lower() in potential_month.lower():
                return potential_category

    return 'Unknown'


def detect_month(filename):
    """Extract month name from filename. Works with both separators.
    e.g. 'doc_xxx_Switchboard-April.csv' -> 'April'
         'doc_xxx_Switchboard June.csv' -> 'June'
    """
    base = os.path.splitext(os.path.basename(filename))[0]
    parts = base.split('_')
    if len(parts) < 2:
        return None

    last_part = parts[-1]

    # Try space split first
    space_split = last_part.rsplit(' ', 1)
    if len(space_split) >= 2:
        potential_month = space_split[-1].strip()
        for k, v in MONTH_MAP.items():
            if k.lower() in potential_month.lower():
                return v

    # Try hyphen split
    hyphen_split = last_part.rsplit('-', 1)
    if len(hyphen_split) >= 2:
        potential_month = hyphen_split[-1].strip()
        for k, v in MONTH_MAP.items():
            if k.lower() in potential_month.lower():
                return v

    return None


def parse_duration(dur_str):
    """Parse Genesys duration string ' 00:04:12.710' to total seconds."""
    if dur_str is None:
        return None
    s = str(dur_str).strip()
    if not s:
        return None
    if ':' in s:
        parts = s.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def classify_outcome(success_str, abandoned_str):
    """Classify call outcome based on Genesys Outcome Success and Abandoned flags."""
    outcome_success = str(success_str).strip() == "1"
    abandoned_flag = str(abandoned_str).strip() == "YES"
    if outcome_success and not abandoned_flag:
        return "successful"
    elif abandoned_flag:
        return "abandoned"
    else:
        return "failed"


def read_raw_csvs(only_category=None):
    """Read all CSVs from CSV Files/ directory, optionally filtered by category."""
    all_rows = []
    file_months = {}  # filename -> {category, month, path}
    for fname in sorted(os.listdir(CSV_DIR)):
        if not fname.endswith('.csv'):
            continue
        filepath = os.path.join(CSV_DIR, fname)
        category = detect_category(fname)
        month = detect_month(fname)
        if not month:
            continue
        if only_category and category.lower() != only_category.lower():
            continue
        file_months[fname] = {
            'category': category,
            'month': month,
            'path': filepath,
        }
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['_filename'] = fname
                row['_category'] = category
                row['_month'] = month
                all_rows.append(row)
    return all_rows, file_months


def extract_kpi_data(rows):
    """Extract total/successful/failed/abandoned calls per month and overall."""
    monthly = defaultdict(lambda: {'total': 0, 'successful': 0, 'failed': 0, 'abandoned': 0})
    overall = {'total': 0, 'successful': 0, 'failed': 0, 'abandoned': 0}

    for row in rows:
        month = row.get('_month', 'Unknown')
        success = classify_outcome(row.get('Outcome Success', ''), row.get('Abandoned', ''))
        monthly[month]['total'] += 1
        overall['total'] += 1
        if success == 'successful':
            monthly[month]['successful'] += 1
            overall['successful'] += 1
        elif success == 'failed':
            monthly[month]['failed'] += 1
            overall['failed'] += 1
        elif success == 'abandoned':
            monthly[month]['abandoned'] += 1
            overall['abandoned'] += 1

    lines = ['Month,Total,Successful,Failed,Abandoned,Success%,Fail%,Abandon%\n']
    months_sorted = sorted(monthly.keys(), key=parse_month_sort_key)
    for month in months_sorted:
        d = monthly[month]
        total = d['total'] or 1
        success_pct = round(d['successful'] / total * 100, 1)
        fail_pct = round(d['failed'] / total * 100, 1)
        abandon_pct = round(d['abandoned'] / total * 100, 1)
        lines.append(f'{month},{d["total"]},{d["successful"]},{d["failed"]},{d["abandoned"]},{success_pct},{fail_pct},{abandon_pct}\n')
    # Total row
    o = overall
    total = o['total'] or 1
    lines.append(f'Total,{o["total"]},{o["successful"]},{o["failed"]},{o["abandoned"]},{round(o["successful"]/total*100,1)},{round(o["failed"]/total*100,1)},{round(o["abandoned"]/total*100,1)}\n')

    return ''.join(lines)


def extract_duration_data(rows):
    """Extract duration statistics (Avg, P50, P95, Max) per month."""
    monthly_durations = defaultdict(list)

    for row in rows:
        month = row.get('_month', 'Unknown')
        dur = parse_duration(row.get('Duration', ''))
        if dur is not None and dur <= 86400:  # filter outliers > 24 hours
            monthly_durations[month].append(dur)

    lines = ['Month,Avg Duration (s),P50 Duration (s),P95 Duration (s),Max Duration (s),Valid Samples\n']
    months_sorted = sorted(monthly_durations.keys(), key=parse_month_sort_key)

    for month in months_sorted:
        durs = sorted(monthly_durations[month])
        if not durs:
            lines.append(f'{month},0,0,0,0,0\n')
            continue
        avg_d = sum(durs) / len(durs)
        p50_d = durs[int(len(durs) * 0.5)]
        p95_d = durs[int(len(durs) * 0.95)]
        max_d = max(durs)
        lines.append(f'{month},{avg_d:.1f},{p50_d:.1f},{p95_d:.1f},{max_d:.1f},{len(durs)}\n')

    return ''.join(lines)


def extract_hourly_data(rows):
    """Extract call counts by hour of day per month."""
    monthly_hours = defaultdict(lambda: defaultdict(int))

    for row in rows:
        month = row.get('_month', 'Unknown')
        date_str = row.get('Date', '')
        if date_str and ':' in str(date_str):
            try:
                dt = datetime.strptime(str(date_str).strip(), '%m/%d/%y %I:%M %p')
                monthly_hours[month][dt.hour] += 1
            except (ValueError, TypeError):
                pass

    months_sorted = sorted(monthly_hours.keys(), key=parse_month_sort_key)

    # Collect all hours
    all_hours = set()
    for m_hours in monthly_hours.values():
        all_hours.update(m_hours.keys())
    if not all_hours:
        all_hours = range(24)
    hours_sorted = sorted(all_hours)

    lines = ['Hour,' + ','.join(months_sorted) + ',All\n']
    for hour in hours_sorted:
        values = [str(monthly_hours[m].get(hour, 0)) for m in months_sorted]
        total = sum(monthly_hours[m].get(hour, 0) for m in months_sorted)
        lines.append(f'{hour},{",".join(values)},{total}\n')

    return ''.join(lines)


def extract_transfer_data(rows):
    """Extract transfer counts and rates per month."""
    monthly = defaultdict(lambda: {'total': 0, 'blind': 0, 'consult': 0})

    for row in rows:
        month = row.get('_month', 'Unknown')
        monthly[month]['total'] += 1
        consult_transferred = str(row.get('Consult Transferred', '')).strip()
        blind_transferred = str(row.get('Blind Transferred', '')).strip()
        transferred = str(row.get('Transferred', '')).strip()

        if transferred == 'YES':
            if consult_transferred == 'YES':
                monthly[month]['consult'] += 1
            elif blind_transferred == 'YES':
                monthly[month]['blind'] += 1

    lines = ['Month,Total Transfers,Blind Transfers,Consult Transfers,Transfer Rate (%)\n']
    months_sorted = sorted(monthly.keys(), key=parse_month_sort_key)

    for month in months_sorted:
        d = monthly[month]
        total = d['total']
        blind = d['blind']
        consult = d['consult']
        transfer_rate = round((blind + consult) / total * 100, 1) if total else 0
        lines.append(f'{month},{blind + consult},{blind},{consult},{transfer_rate}\n')

    return ''.join(lines)


def extract_queue_paths(rows):
    """Extract call flow paths from the Queue column of raw CSVs."""
    path_counter = Counter()
    monthly_paths = defaultdict(Counter)

    for row in rows:
        month = row.get('_month', 'Unknown')
        queue = row.get('Queue', '')
        if not queue or str(queue).strip() == '':
            continue
        queue_str = str(queue).strip()
        # Queue column contains semicolon-separated path segments
        path_str = queue_str.replace(';', ' -> ').strip()
        if path_str:
            path_counter[path_str] += 1
            monthly_paths[month][path_str] += 1

    return path_counter, monthly_paths


def extract_disconnect_data(rows):
    """Extract disconnect type counts per month."""
    monthly_disconnects = defaultdict(Counter)

    for row in rows:
        month = row.get('_month', 'Unknown')
        disconnect = row.get('Disconnect Type', '')
        all_flow_disconnect = row.get('All Flow Disconnect', '')
        # Use All Flow Disconnect as it captures the full path
        disconnect_str = str(all_flow_disconnect).strip() if all_flow_disconnect else str(disconnect).strip()
        if disconnect_str:
            monthly_disconnects[month][disconnect_str] += 1

    # Aggregate
    overall = Counter()
    for m_counter in monthly_disconnects.values():
        overall.update(m_counter)

    # Get top disconnect types
    top_types = overall.most_common(50)

    months_sorted = sorted(monthly_disconnects.keys(), key=parse_month_sort_key)
    all_months = sorted(monthly_disconnects.keys(), key=parse_month_sort_key)

    lines = ['Disconnect Type,' + ','.join(all_months) + ',Total\n']
    for dtype, total_count in top_types:
        values = [str(monthly_disconnects[m].get(dtype, 0)) for m in all_months]
        # Escape quotes in disconnect type
        escaped_dtype = '"' + dtype.replace('"', '""') + '"'
        lines.append(f'{escaped_dtype},{",".join(values)},{total_count}\n')

    return ''.join(lines)


def extract_queue_summary(rows):
    """Extract queue segment count statistics per month."""
    monthly_counts = defaultdict(list)

    for row in rows:
        month = row.get('_month', 'Unknown')
        queue_segs = row.get('Queue Segments', '')
        try:
            count = int(str(queue_segs).strip())
            if count > 0:
                monthly_counts[month].append(count)
        except (ValueError, TypeError):
            pass

    lines = ['Month,Total Calls,Has Queue Data,Queue Data %,Avg Queue Segments\n']
    months_sorted = sorted(monthly_counts.keys(), key=parse_month_sort_key)

    for month in months_sorted:
        # Total calls for this month
        total = sum(1 for r in rows if r.get('_month') == month)
        has_queue = len(monthly_counts[month])
        avg_segs = sum(monthly_counts[month]) / len(monthly_counts[month]) if monthly_counts[month] else 0
        pct = round(has_queue / total * 100, 1) if total else 0
        lines.append(f'{month},{total},{has_queue},{pct},{avg_segs:.1f}\n')

    return ''.join(lines)


def extract_queue_waits(rows):
    """Extract queue wait time statistics per month."""
    monthly_waits = defaultdict(list)

    for row in rows:
        month = row.get('_month', 'Unknown')
        total_hold = parse_duration(row.get('Total Hold', ''))
        if total_hold is not None and total_hold > 0:
            monthly_waits[month].append(total_hold)

    lines = ['Month,Total Calls,Has Hold Data,Hold Data %,Avg Hold (s),P50 Hold (s),Max Hold (s)\n']
    months_sorted = sorted(monthly_waits.keys(), key=parse_month_sort_key)

    for month in months_sorted:
        total = sum(1 for r in rows if r.get('_month') == month)
        has_hold = len(monthly_waits[month])
        waits = sorted(monthly_waits[month])
        avg_wait = sum(waits) / len(waits) if waits else 0
        p50_wait = waits[int(len(waits) * 0.5)] if waits else 0
        max_wait = max(waits) if waits else 0
        pct = round(has_hold / total * 100, 1) if total else 0
        lines.append(f'{month},{total},{has_hold},{pct},{avg_wait:.1f},{p50_wait:.1f},{max_wait:.1f}\n')

    return ''.join(lines)


def write_csv(filepath, content):
    """Write CSV content to file, creating directories if needed."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        f.write(content)


def main_wrapper(category):
    """Process a specific category and generate all CSVs."""
    rows, file_months = read_raw_csvs(only_category=category)
    prefix = category

    os.makedirs(CHARTS_DIR, exist_ok=True)

    # Generate outcomes CSV
    outcomes_data = extract_kpi_data(rows)
    write_csv(os.path.join(CHARTS_DIR, f'{prefix}_outcomes.csv'), outcomes_data)

    # Generate duration CSV
    write_csv(os.path.join(CHARTS_DIR, f'{prefix}_duration.csv'), extract_duration_data(rows))

    # Generate hourly CSV
    write_csv(os.path.join(CHARTS_DIR, f'{prefix}_hourly.csv'), extract_hourly_data(rows))

    # Generate transfers CSV
    write_csv(os.path.join(CHARTS_DIR, f'{prefix}_transfers.csv'), extract_transfer_data(rows))

    # Generate disconnect types CSV
    write_csv(os.path.join(CHARTS_DIR, f'{prefix}_disconnect_types.csv'), extract_disconnect_data(rows))

    # Extract Queue paths
    path_counter, monthly_paths = extract_queue_paths(rows)

    # Save aggregated flow paths
    path_lines = ['Path,Count\n']
    for path, count in path_counter.most_common():
        path_lines.append(f'{path},{count}\n')
    write_csv(os.path.join(CHARTS_DIR, f'{prefix}_flow_paths.csv'), ''.join(path_lines))

    # Save per-month flow paths
    for month, m_paths in monthly_paths.items():
        m_lines = ['Path,Count\n']
        for path, count in m_paths.most_common():
            m_lines.append(f'{path},{count}\n')
        write_csv(os.path.join(CHARTS_DIR, f'{prefix}_flow_paths_{month.lower()}.csv'), ''.join(m_lines))

    # Generate queue summary
    write_csv(os.path.join(CHARTS_DIR, f'{prefix}_queue_summary.csv'), extract_queue_summary(rows))

    # Generate queue waits
    write_csv(os.path.join(CHARTS_DIR, f'{prefix}_queue_waits.csv'), extract_queue_waits(rows))

    # Generate summary CSV
    total_calls = len(rows)

    # Parse outcome lines into a dict for easy lookup
    outcome_rows_parsed = []
    for line in outcomes_data.strip().split('\n')[1:]:  # skip header
        if line.strip():
            outcome_rows_parsed.append(dict(zip(['Month', 'Total', 'Successful', 'Failed', 'Abandoned', 'Success%', 'Fail%', 'Abandon%'], line.split(','))))

    # Get ordered months (skip 'Total' row)
    months_in_outcome = [r['Month'] for r in outcome_rows_parsed if r['Month'] != 'Total']
    ordered_months = sorted(months_in_outcome, key=parse_month_sort_key)

    summary_lines = ['Metric,April,May,June,Total\n']
    if ordered_months:
        for metric_idx, metric_name in enumerate(['Total Calls', 'Successful', 'Failed', 'Abandoned']):
            col_name = ['Total', 'Successful', 'Failed', 'Abandoned'][metric_idx]
            vals = []
            for m in ordered_months:
                for r in outcome_rows_parsed:
                    if r.get('Month', '').strip() == m and r.get(col_name):
                        vals.append(r[col_name])
                        break
                else:
                    vals.append('0')
            total_val = sum(int(v) for v in vals if v and v != '0')
            summary_lines.append(f'{metric_name},{",".join(vals)},{total_val}\n')

    write_csv(os.path.join(CHARTS_DIR, f'{prefix}_summary.csv'), ''.join(summary_lines))

    print(f"  {total_calls} rows, {len(path_counter)} unique paths")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main_wrapper(sys.argv[1])
    else:
        all_rows, file_months = read_raw_csvs()
        categories = defaultdict(list)
        for fname, info in file_months.items():
            categories[info['category']].append(fname)
        for category in sorted(categories.keys()):
            print(f"Processing category: {category}")
            main_wrapper(category)
        print(f"\nDone. Processed {len(all_rows)} total rows across {len(categories)} categories.")
