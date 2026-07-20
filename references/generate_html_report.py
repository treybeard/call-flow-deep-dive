#!/usr/bin/env python3
"""Generate HTML dashboard from CSV reports.

Reads CSV data from Reports/Charts/ and creates an HTML dashboard with
matplotlib charts for each tab.

Usage:
    cd scripts
    python3 generate_html_report.py
    # or specify category:
    python3 generate_html_report.py Switchboard
"""

import os
import sys
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(PROJECT_DIR, "Reports_HTML", "charts")
REPORTS_DIR = os.path.join(PROJECT_DIR, "Reports", "Charts")

COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8',
}


def read_csv(filepath):
    """Read CSV file and return list of dicts."""
    rows = []
    if not os.path.exists(filepath):
        return rows
    with open(filepath, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def create_summary_charts(outcomes, duration):
    """Create KPI cards and monthly comparison chart from outcomes and duration data."""
    charts = []

    # Extract months (skip 'Total' row)
    months = [r['Month'] for r in outcomes if r['Month'] != 'Total']

    # KPI values
    total_calls = sum(int(r['Total']) for r in outcomes if r['Month'] != 'Total')
    total_abandoned = sum(int(r['Abandoned']) for r in outcomes if r['Month'] != 'Total')
    total_successful = sum(int(r['Successful']) for r in outcomes if r['Month'] != 'Total')
    abandon_rate = round(total_abandoned / total_calls * 100, 1) if total_calls else 0
    success_rate = round(total_successful / total_calls * 100, 1) if total_calls else 0

    # Avg duration
    avg_durations = [float(r['Avg Duration (s)']) for r in duration if r['Month'] != 'Total']
    overall_avg = sum(avg_durations) / len(avg_durations) if avg_durations else 0

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    kpis = [
        (f'{total_calls:,}', 'Total Calls'),
        (f'{abandon_rate}%', 'Abandonment Rate'),
        (f'{success_rate}%', 'Success Rate'),
        (f'{overall_avg:.0f}s', 'Avg Duration'),
    ]
    for i, (value, label) in enumerate(kpis):
        ax = axes[i // 2, i % 2]
        ax.axis('off')
        ax.text(0.5, 0.5, value, ha='center', va='center', fontsize=32, fontweight='bold', color=COLORS['primary'])
        ax.text(0.5, 0.2, label, ha='center', va='center', fontsize=14, color='#666')
    plt.suptitle('Key Performance Indicators', fontsize=16, fontweight='bold')
    plt.tight_layout()
    chart_path = os.path.join(CHARTS_DIR, 'summary_kpis.png')
    fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig)
    charts.append(('summary_kpis.png', 'KPI Cards'))

    # Monthly comparison
    monthly_data = {r['Month']: {
        'Total': int(r['Total']),
        'Successful': int(r['Successful']),
        'Failed': int(r['Failed']),
        'Abandoned': int(r['Abandoned']),
    } for r in outcomes if r['Month'] != 'Total'}

    months_sorted = sorted(monthly_data.keys(), key=lambda m: ['January','February','March','April','May','June','July','August','September','October','November','December'].index(m) if m in ['January','February','March','April','May','June','July','August','September','October','November','December'] else 99)
    metrics = ['Total', 'Successful', 'Failed', 'Abandoned']

    fig, ax = plt.subplots(figsize=(12, 7))
    x = range(len(months_sorted))
    width = 0.15

    for i, metric in enumerate(metrics):
        values = [monthly_data[m][metric] for m in months_sorted]
        offset = (i - 1.5) * width
        ax.bar([p + offset for p in x], values, width, label=metric)

    ax.set_xlabel('Month')
    ax.set_ylabel('Value')
    ax.set_title('Monthly Summary Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(months_sorted)
    ax.legend(loc='upper right', fontsize=9)

    chart_path = os.path.join(CHARTS_DIR, 'monthly_summary.png')
    fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig)
    charts.append(('monthly_summary.png', 'Monthly Summary Comparison'))

    return charts


def create_monthly_charts(month_name, outcomes, duration, flow_paths_month):
    """Create monthly charts: call distribution, duration, top paths."""
    charts = []

    # Get this month's data
    month_outcome = next((r for r in outcomes if r['Month'] == month_name), None)
    month_dur = next((r for r in duration if r['Month'] == month_name), None)

    if not month_outcome:
        return charts

    # Call distribution pie chart
    labels = ['Successful', 'Failed', 'Abandoned']
    values = [
        int(month_outcome.get('Successful', 0)),
        int(month_outcome.get('Failed', 0)),
        int(month_outcome.get('Abandoned', 0)),
    ]

    if sum(values) > 0:
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90,
               colors=[COLORS['success'], COLORS['danger'], COLORS['warning']])
        ax.set_title(f'{month_name} 2026 - Call Distribution', fontsize=14, fontweight='bold')
        chart_path = os.path.join(CHARTS_DIR, f'{month_name.lower()}_call_distribution.png')
        fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close(fig)
        charts.append((f'{month_name.lower()}_call_distribution.png', f'{month_name} 2026 - Call Distribution'))

    # Duration comparison bar chart
    if month_dur:
        avg_dur = float(month_dur.get('Avg Duration (s)', 0))
        p50_dur = float(month_dur.get('P50 Duration (s)', 0))
        p95_dur = float(month_dur.get('P95 Duration (s)', 0))

        fig, ax = plt.subplots(figsize=(8, 6))
        durations = [avg_dur, p50_dur, p95_dur]
        duration_labels = ['Avg Duration', 'P50 Duration', 'P95 Duration']
        bars = ax.bar(duration_labels, durations, color=[COLORS['info'], COLORS['primary'], COLORS['secondary']],
                      edgecolor='white', linewidth=2)
        ax.set_ylabel('Duration (MM:SS)')
        ax.set_title(f'{month_name} 2026 - Duration Statistics', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # Format y-axis tick labels to MM:SS
        def format_mmss(seconds):
            m = int(seconds) // 60
            s = int(seconds) % 60
            return f'{m:02d}:{s:02d}'
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: format_mmss(val)))

        for bar, duration in zip(bars, durations):
            height = bar.get_height()
            m, s = int(duration) // 60, int(duration) % 60
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{m:02d}:{s:02d}', ha='center', va='bottom', fontweight='bold', fontsize=11)

        chart_path = os.path.join(CHARTS_DIR, f'{month_name.lower()}_duration.png')
        fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close(fig)
        charts.append((f'{month_name.lower()}_duration.png', f'{month_name} Duration Statistics'))

    # Top call paths
    if flow_paths_month:
        paths = [(r['Path'], int(r['Count'])) for r in flow_paths_month]
        paths.sort(key=lambda x: x[1], reverse=True)
        top_paths = paths[:10]

        if top_paths:
            fig, ax = plt.subplots(figsize=(10, 6))
            y_pos = range(len(top_paths))
            counts = [p[1] for p in top_paths]

            bars = ax.barh(y_pos, counts, color=COLORS['primary'], edgecolor='white', linewidth=1)
            ax.set_yticks(y_pos)
            ax.set_yticklabels([f"#{i+1} {p[0][:40]}" for i, p in enumerate(top_paths)], fontsize=9)
            ax.set_xlabel('Number of Calls')
            ax.set_title(f'Top 10 Call Flow Paths - {month_name} 2026', fontsize=14, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)

            for i, (bar, count) in enumerate(zip(bars, counts)):
                ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                        f'{count:,}', ha='left', va='center', fontweight='bold', fontsize=10)

            chart_path = os.path.join(CHARTS_DIR, f'{month_name.lower()}_top_paths.png')
            fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
            plt.close(fig)
            charts.append((f'{month_name.lower()}_top_paths.png', f'{month_name} Top Call Flow Paths'))

    return charts


def create_transfers_charts(transfers):
    """Create transfer patterns chart."""
    charts = []

    if not transfers:
        return charts

    months = [r['Month'] for r in transfers]
    counts = [int(r['Total Transfers']) for r in transfers]
    rates = [float(r['Transfer Rate (%)']) for r in transfers]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    x = range(len(months))
    width = 0.35

    ax1.bar([p + width/2 for p in x], counts, width, label='Transfer Count', color=COLORS['primary'])
    ax2 = ax1.twinx()
    ax2.plot([p + width/2 for p in x], rates, 'o-', color=COLORS['danger'], linewidth=2, label='Transfer Rate')

    ax1.set_xlabel('Month')
    ax1.set_ylabel('Transfer Count', color=COLORS['primary'])
    ax2.set_ylabel('Transfer Rate (%)', color=COLORS['danger'])
    ax1.set_title('Transfer Patterns', fontsize=14, fontweight='bold')
    ax1.set_xticks([p + width/2 for p in x])
    ax1.set_xticklabels(months)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    ax1.grid(alpha=0.3)

    chart_path = os.path.join(CHARTS_DIR, 'transfers.png')
    fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig)
    charts.append(('transfers.png', 'Transfer Patterns'))

    return charts


def create_disconnect_charts(disconnects):
    """Create disconnect types chart."""
    charts = []

    if not disconnects:
        return charts

    # Get top 10 by total
    top_disconnects = sorted(disconnects, key=lambda r: int(r.get('Total', 0)), reverse=True)[:10]

    if top_disconnects:
        labels = [r['Disconnect Type'][:50] + ('...' if len(r['Disconnect Type']) > 50 else '') for r in top_disconnects]
        counts = [int(r['Total']) for r in top_disconnects]

        fig, ax = plt.subplots(figsize=(14, 8))
        y_pos = range(len(labels))
        bars = ax.barh(y_pos, counts, color=COLORS['danger'], edgecolor='white', linewidth=1, height=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_xlabel('Number of Calls')
        ax.set_title('Top 10 Disconnect Types', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                    f'{count:,}', ha='left', va='center', fontweight='bold', fontsize=11)

        chart_path = os.path.join(CHARTS_DIR, 'disconnect_types.png')
        fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close(fig)
        charts.append(('disconnect_types.png', 'Disconnect Types'))

    return charts


def create_hourly_charts(hourly):
    """Create hourly distribution chart (hours 6-18 only)."""
    charts = []

    if not hourly:
        return charts

    # Get month columns
    months = [k for k in hourly[0].keys() if k not in ('Hour', 'All')]

    # Filter to hours 6-18
    hourly_filtered = [r for r in hourly if 6 <= int(r['Hour']) <= 18]

    fig, ax = plt.subplots(figsize=(12, 6))
    for month in months:
        hours = [int(r['Hour']) for r in hourly_filtered]
        values = [int(r.get(month, 0)) for r in hourly_filtered]
        ax.plot(hours, values, marker='o', linewidth=2, label=month)

    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Number of Calls')
    ax.set_title('Hourly Call Distribution (6 AM - 6 PM)', fontsize=14, fontweight='bold')
    ax.set_xticks(sorted([int(r['Hour']) for r in hourly_filtered]))
    ax.legend()
    ax.grid(alpha=0.3)

    chart_path = os.path.join(CHARTS_DIR, 'hourly_distribution.png')
    fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig)
    charts.append(('hourly_distribution.png', 'Hourly Distribution'))

    return charts


def create_duration_stats_charts(duration):
    """Create duration statistics chart with MM:SS format."""
    charts = []

    if not duration:
        return charts

    months = [r['Month'] for r in duration]
    avg_vals = [float(r['Avg Duration (s)']) for r in duration]
    p50_vals = [float(r['P50 Duration (s)']) for r in duration]
    p95_vals = [float(r['P95 Duration (s)']) for r in duration]
    max_vals = [float(r['Max Duration (s)']) for r in duration]

    x = range(len(months))
    width = 0.2

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar([p + 0*width for p in x], avg_vals, width, label='Avg', color=COLORS['primary'])
    ax.bar([p + 1*width for p in x], p50_vals, width, label='P50', color=COLORS['info'])
    ax.bar([p + 2*width for p in x], p95_vals, width, label='P95', color=COLORS['secondary'])
    ax.bar([p + 3*width for p in x], max_vals, width, label='Max', color=COLORS['warning'])

    ax.set_xlabel('Metric')
    ax.set_ylabel('Duration (MM:SS)')
    ax.set_title('Duration Statistics by Month', fontsize=14, fontweight='bold')
    ax.set_xticks([p + 1.5*width for p in x])
    ax.set_xticklabels(months)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Format y-axis tick labels to MM:SS
    def format_mmss(seconds):
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f'{m:02d}:{s:02d}'
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: format_mmss(val)))

    # Add MM:SS labels on bars
    all_patches = ax.patches
    idx = 0
    for i in range(len(months)):
        for j in range(4):
            if idx < len(all_patches):
                bar = all_patches[idx]
                height = bar.get_height()
                m, s = int(height) // 60, int(height) % 60
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{m:02d}:{s:02d}', ha='center', va='bottom', fontsize=8)
                idx += 1

    chart_path = os.path.join(CHARTS_DIR, 'duration_stats.png')
    fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig)
    charts.append(('duration_stats.png', 'Duration Statistics'))

    return charts


def create_outcomes_charts(outcomes):
    """Create outcomes stacked bar chart."""
    charts = []

    if not outcomes:
        return charts

    months = [r['Month'] for r in outcomes if r['Month'] != 'Total']
    successful = [int(r['Successful']) for r in outcomes if r['Month'] != 'Total']
    failed = [int(r['Failed']) for r in outcomes if r['Month'] != 'Total']
    abandoned = [int(r['Abandoned']) for r in outcomes if r['Month'] != 'Total']

    x = range(len(months))
    width = 0.6

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x, successful, width, label='Successful', color=COLORS['success'])
    ax.bar(x, failed, width, bottom=successful, label='Failed', color=COLORS['danger'])
    ax.bar(x, abandoned, width, bottom=[s+f for s, f in zip(successful, failed)],
           label='Abandoned', color=COLORS['warning'])

    ax.set_xlabel('Month')
    ax.set_ylabel('Number of Calls')
    ax.set_title('Call Outcomes', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    chart_path = os.path.join(CHARTS_DIR, 'outcomes.png')
    fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig)
    charts.append(('outcomes.png', 'Call Outcomes'))

    return charts


def create_flow_paths_charts(flow_paths):
    """Create flow paths chart."""
    charts = []

    if not flow_paths:
        return charts

    paths = [(r['Path'], int(r['Count'])) for r in flow_paths]
    paths.sort(key=lambda x: x[1], reverse=True)
    top_paths = paths[:15]

    if top_paths:
        fig, ax = plt.subplots(figsize=(12, 8))
        y_pos = range(len(top_paths))
        counts = [p[1] for p in top_paths]

        bars = ax.barh(y_pos, counts, color=COLORS['secondary'], edgecolor='white', linewidth=1)
        ax.set_yticks(y_pos)
        ax.set_yticklabels([p[0][:60] + ('...' if len(p[0]) > 60 else '') for p in top_paths], fontsize=9)
        ax.set_xlabel('Number of Calls')
        ax.set_title('Top 15 Call Flow Paths', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                    f'{count:,}', ha='left', va='center', fontweight='bold', fontsize=10)

        chart_path = os.path.join(CHARTS_DIR, 'flow_paths.png')
        fig.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close(fig)
        charts.append(('flow_paths.png', 'Call Flow Paths'))

    return charts


def generate_html(category='Switchboard'):
    """Generate HTML dashboard from CSV data."""
    os.makedirs(CHARTS_DIR, exist_ok=True)

    # Read CSV data
    outcomes = read_csv(os.path.join(REPORTS_DIR, f'{category}_outcomes.csv'))
    duration = read_csv(os.path.join(REPORTS_DIR, f'{category}_duration.csv'))
    hourly = read_csv(os.path.join(REPORTS_DIR, f'{category}_hourly.csv'))
    transfers = read_csv(os.path.join(REPORTS_DIR, f'{category}_transfers.csv'))
    disconnects = read_csv(os.path.join(REPORTS_DIR, f'{category}_disconnect_types.csv'))
    flow_paths_all = read_csv(os.path.join(REPORTS_DIR, f'{category}_flow_paths.csv'))

    # Read monthly flow paths
    months = [r['Month'] for r in outcomes if r['Month'] != 'Total']
    monthly_flow_paths = {}
    for month in months:
        monthly_flow_paths[month] = read_csv(os.path.join(REPORTS_DIR, f'{category}_flow_paths_{month.lower()}.csv'))

    all_charts = []

    # Summary charts
    all_charts.extend(create_summary_charts(outcomes, duration))

    # Monthly charts
    for month in months:
        all_charts.extend(create_monthly_charts(month, outcomes, duration, monthly_flow_paths.get(month, [])))

    # Other charts
    all_charts.extend(create_transfers_charts(transfers))
    all_charts.extend(create_disconnect_charts(disconnects))
    all_charts.extend(create_hourly_charts(hourly))
    all_charts.extend(create_duration_stats_charts(duration))
    all_charts.extend(create_outcomes_charts(outcomes))
    all_charts.extend(create_flow_paths_charts(flow_paths_all))

    # Build chart HTML blocks
    charts_html = '\n'.join([
        f'''
        <div class="chart-card">
            <h3>{name}</h3>
            <img src="charts/{file}" alt="{name}" class="chart-image">
        </div>'''
        for file, name in all_charts
    ])

    # Build monthly tables from outcomes data
    monthly_rows = [r for r in outcomes if r['Month'] != 'Total']

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{category} Deep-Dive Analysis</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #F8F9FA;
            color: #2C3E50;
            line-height: 1.6;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
            color: #2E86AB;
            font-size: 28px;
        }}
        h2 {{
            margin: 30px 0 15px;
            color: #2E86AB;
            border-bottom: 2px solid #2E86AB;
            padding-bottom: 5px;
        }}
        h3 {{
            margin-bottom: 10px;
            color: #34495E;
            font-size: 16px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .kpi-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .kpi-value {{
            font-size: 32px;
            font-weight: bold;
            color: #2E86AB;
        }}
        .kpi-label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-image {{
            width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        th {{
            background: #2E86AB;
            color: white;
            padding: 12px 15px;
            text-align: center;
            font-weight: 600;
        }}
        td {{
            padding: 10px 15px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }}
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        tr:hover {{
            background: #e9ecef;
        }}
        .section {{
            margin-bottom: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{category} Deep-Dive Analysis</h1>

        <div class="section">
            <h2>Key Performance Indicators</h2>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-value">{total_calls:,.0f if monthly_rows else 0}</div>
                    <div class="kpi-label">Total Calls</div>
                </div>
                <div class="kpi-card">
'''

    # Compute KPIs for the HTML body
    total_calls_count = sum(int(r['Total']) for r in monthly_rows)
    total_abandoned_count = sum(int(r['Abandoned']) for r in monthly_rows)
    total_successful_count = sum(int(r['Successful']) for r in monthly_rows)
    abandon_rate = round(total_abandoned_count / total_calls_count * 100, 1) if total_calls_count else 0
    success_rate = round(total_successful_count / total_calls_count * 100, 1) if total_calls_count else 0
    avg_durs = [float(r['Avg Duration (s)']) for r in duration if r['Month'] != 'Total']
    overall_avg = sum(avg_durs) / len(avg_durs) if avg_durs else 0

    def format_mmss(seconds):
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f'{m:02d}:{s:02d}'

    html += f'''                    <div class="kpi-value">{abandon_rate}%</div>
                    <div class="kpi-label">Abandonment Rate</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{success_rate}%</div>
                    <div class="kpi-label">Success Rate</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{format_mmss(overall_avg)}</div>
                    <div class="kpi-label">Avg Duration</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Charts</h2>
            <div class="chart-grid">
{charts_html}
            </div>
        </div>

        <div class="section">
            <h2>Summary Table</h2>
            <table>
                <thead>
                    <tr>
                        <th>Month</th>
                        <th>Total Calls</th>
                        <th>Successful</th>
                        <th>Failed</th>
                        <th>Abandoned</th>
                        <th>Success %</th>
                        <th>Fail %</th>
                        <th>Abandon %</th>
                    </tr>
                </thead>
                <tbody>
'''

    for r in monthly_rows:
        html += f'''                    <tr>
                        <td>{r.get("Month", "")}</td>
                        <td>{r.get("Total", "0")}</td>
                        <td>{r.get("Successful", "0")}</td>
                        <td>{r.get("Failed", "0")}</td>
                        <td>{r.get("Abandoned", "0")}</td>
                        <td>{r.get("Success%", "0")}%</td>
                        <td>{r.get("Fail%", "0")}%</td>
                        <td>{r.get("Abandon%", "0")}%</td>
                    </tr>
'''

    html += f'''                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Duration Statistics</h2>
            <table>
                <thead>
                    <tr>
                        <th>Month</th>
                        <th>Avg Duration</th>
                        <th>P50 Duration</th>
                        <th>P95 Duration</th>
                        <th>Max Duration</th>
                        <th>Valid Samples</th>
                    </tr>
                </thead>
                <tbody>
'''

    for r in duration:
        try:
            avg_str = format_mmss(float(r.get('Avg Duration (s)', 0)))
            p50_str = format_mmss(float(r.get('P50 Duration (s)', 0)))
            p95_str = format_mmss(float(r.get('P95 Duration (s)', 0)))
            max_str = format_mmss(float(r.get('Max Duration (s)', 0)))
        except (ValueError, TypeError):
            avg_str = p50_str = p95_str = max_str = '00:00'
        html += f'''                    <tr>
                        <td>{r.get("Month", "")}</td>
                        <td>{avg_str}</td>
                        <td>{p50_str}</td>
                        <td>{p95_str}</td>
                        <td>{max_str}</td>
                        <td>{r.get("Valid Samples", "0")}</td>
                    </tr>
'''

    html += f'''                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Transfer Patterns</h2>
            <table>
                <thead>
                    <tr>
                        <th>Month</th>
                        <th>Total Transfers</th>
                        <th>Blind Transfers</th>
                        <th>Consult Transfers</th>
                        <th>Transfer Rate (%)</th>
                    </tr>
                </thead>
                <tbody>
'''

    for r in transfers:
        html += f'''                    <tr>
                        <td>{r.get("Month", "")}</td>
                        <td>{r.get("Total Transfers", "0")}</td>
                        <td>{r.get("Blind Transfers", "0")}</td>
                        <td>{r.get("Consult Transfers", "0")}</td>
                        <td>{r.get("Transfer Rate (%)", "0")}</td>
                    </tr>
'''

    html += f'''                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Hourly Call Distribution (Business Hours 6 AM - 6 PM)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Hour</th>
'''
    for m in months:
        html += f'                        <th>{m}</th>\n'
    html += '                        <th>All</th>\n'
    html += '                    </tr>\n                </thead>\n                <tbody>\n'

    for r in hourly:
        hour = int(r.get('Hour', 0))
        if 6 <= hour <= 18:
            html += f'                    <tr>\n                        <td>{hour}</td>\n'
            for m in months:
                html += f'                        <td>{r.get(m, "0")}</td>\n'
            html += f'                        <td>{r.get("All", "0")}</td>\n'
            html += '                    </tr>\n'

    html += '''                </tbody>
            </table>
        </div>

    </div>
</body>
</html>
'''

    # Write HTML file
    reports_out = os.path.join(PROJECT_DIR, "Reports_HTML")
    os.makedirs(reports_out, exist_ok=True)
    html_path = os.path.join(reports_out, f"report_{category}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Charts generated: {len(all_charts)}")
    print(f"  Saved HTML: {html_path}")
    print(f"  Charts dir:  {CHARTS_DIR}")
    print(f"  Include report_{category}.html and the charts/ folder together when sharing")


def main():
    """Entry point with auto-detect and CLI argument support."""
    if len(sys.argv) > 1:
        category = sys.argv[1]
    else:
        # Auto-detect category from available CSVs
        if os.path.isdir(REPORTS_DIR):
            available = set()
            for fname in os.listdir(REPORTS_DIR):
                if fname.endswith('_outcomes.csv'):
                    available.add(fname.replace('_outcomes.csv', ''))
            if available:
                category = sorted(available)[0]
            else:
                print("No data CSVs found in Reports/Charts/. Run extract_html_data.py first.")
                return
        else:
            print(f"Reports/Charts/ directory not found at {REPORTS_DIR}. Run extract_html_data.py first.")
            return

    print(f"Generating HTML dashboard for category: {category}")
    generate_html(category)


if __name__ == '__main__':
    main()
