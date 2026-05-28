"""
Generate HTML Program Performance Report (POC).
Combines: summary matrix + detail pages for 2 programs with screenshots and monthly trends.
"""
import json
import base64
import os

with open('C:/Users/kseaman/Downloads/Cursor/program_metrics_filtered.json') as f:
    all_programs = json.load(f)

with open('C:/Users/kseaman/Downloads/Cursor/program_monthly.json') as f:
    monthly_data = json.load(f)

def img_to_base64(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

baba_img = img_to_base64('C:/Users/kseaman/Downloads/Cursor/screenshots/screenshot_baba.png')
mba_img = img_to_base64('C:/Users/kseaman/Downloads/Cursor/screenshots/screenshot_mba.png')

poc_programs = {
    'BA in Business Administration': {
        'screenshot': baba_img,
        'url': 'https://www.uagc.edu/online-degrees/bachelors/business-administration',
        'account_group': 'Business'
    },
    'Master of Business Administration': {
        'screenshot': mba_img,
        'url': 'https://www.uagc.edu/online-degrees/masters/business-administration',
        'account_group': 'Business'
    }
}

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>UAGC Program Performance Report - POC</title>
<style>
:root {
    --uagc-red: #CC0033;
    --uagc-dark: #1a1a2e;
    --bg: #f5f7fa;
    --card: #ffffff;
    --border: #e2e8f0;
    --text: #334155;
    --muted: #64748b;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
.container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
h1 { color: var(--uagc-dark); font-size: 2rem; margin-bottom: 0.5rem; }
.subtitle { color: var(--muted); margin-bottom: 2rem; }
.card { background: var(--card); border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); padding: 1.5rem; margin-bottom: 2rem; }
.card h2 { color: var(--uagc-dark); margin-bottom: 1rem; font-size: 1.3rem; border-bottom: 2px solid var(--uagc-red); padding-bottom: 0.5rem; display: inline-block; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th { background: var(--uagc-dark); color: white; padding: 0.6rem 0.8rem; text-align: left; position: sticky; top: 0; }
th:nth-child(n+3) { text-align: right; }
td { padding: 0.5rem 0.8rem; border-bottom: 1px solid var(--border); }
td:nth-child(n+3) { text-align: right; font-variant-numeric: tabular-nums; }
tr:hover { background: #f0f4ff; }
.highlight { background: #fffbeb !important; font-weight: 600; }
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.kpi { background: linear-gradient(135deg, var(--uagc-dark), #2d2d5e); color: white; border-radius: 10px; padding: 1.2rem; text-align: center; }
.kpi .value { font-size: 1.8rem; font-weight: 700; }
.kpi .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8; margin-top: 0.3rem; }
.detail-section { page-break-before: always; margin-top: 3rem; }
.detail-header { display: flex; align-items: flex-start; gap: 2rem; margin-bottom: 1.5rem; }
.detail-info { flex: 1; }
.detail-info h3 { font-size: 1.5rem; color: var(--uagc-dark); }
.detail-info .meta { color: var(--muted); font-size: 0.9rem; margin-top: 0.3rem; }
.detail-info .meta a { color: var(--uagc-red); text-decoration: none; }
.screenshot-container { margin: 1.5rem 0; }
.screenshot-container img { max-width: 100%; border-radius: 8px; border: 1px solid var(--border); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.trend-table th { background: var(--uagc-red); }
.funnel-bar { display: flex; align-items: center; gap: 0.5rem; margin: 0.3rem 0; }
.funnel-bar .bar { height: 20px; background: var(--uagc-red); border-radius: 3px; min-width: 2px; }
.funnel-bar .bar-label { font-size: 0.75rem; color: var(--muted); min-width: 80px; }
.toc { margin-bottom: 2rem; }
.toc a { color: var(--uagc-red); text-decoration: none; margin-right: 1rem; }
@media print {
    .container { max-width: 100%; }
    .detail-section { page-break-before: always; }
}
</style>
</head>
<body>
<div class="container">
    <h1>UAGC Program Performance Report</h1>
    <p class="subtitle">Lead Funnel Analysis | Dec 20, 2025 - May 20, 2026 (6 months) | 69 Programs from Master List</p>

    <nav class="toc">
        <strong>Jump to:</strong>
        <a href="#matrix">Summary Matrix</a>
        <a href="#detail-baba">BA in Business Administration</a>
        <a href="#detail-mba">Master of Business Administration</a>
    </nav>

    <!-- SUMMARY MATRIX -->
    <div class="card" id="matrix">
        <h2>Summary Matrix - All Programs</h2>
        <div style="max-height: 600px; overflow-y: auto;">
        <table>
            <thead>
                <tr>
                    <th style="min-width:280px">Program Name</th>
                    <th>Level</th>
                    <th>Leads</th>
                    <th>Apps Started</th>
                    <th>Decisions</th>
                    <th>New Enrollments</th>
                    <th>App Start %</th>
                    <th>Decision %</th>
                    <th>Enrollment %</th>
                </tr>
            </thead>
            <tbody>
"""

for p in all_programs:
    name = p['program_name'] or '(Unknown)'
    highlight = ' class="highlight"' if name in poc_programs else ''
    html += f"""                <tr{highlight}>
                    <td>{name}</td>
                    <td>{p['degree_level'] or ''}</td>
                    <td>{p['leads']:,}</td>
                    <td>{p['apps_started']:,}</td>
                    <td>{p['decisions']:,}</td>
                    <td>{p['new_enrollments']:,}</td>
                    <td>{p['app_start_rate']:.1f}%</td>
                    <td>{p['decision_rate']:.1f}%</td>
                    <td>{p['enrollment_rate']:.1f}%</td>
                </tr>
"""

html += """            </tbody>
        </table>
        </div>
    </div>

"""

# Detail pages for POC programs
detail_configs = [
    ('detail-baba', 'BA in Business Administration'),
    ('detail-mba', 'Master of Business Administration'),
]

for anchor, prog_name in detail_configs:
    prog_info = poc_programs[prog_name]
    metrics = next((p for p in all_programs if p['program_name'] == prog_name), None)
    months = monthly_data.get(prog_name, [])
    
    if not metrics:
        continue
    
    max_leads = max(m['leads'] for m in months) if months else 1
    
    html += f"""    <!-- DETAIL: {prog_name} -->
    <div class="detail-section card" id="{anchor}">
        <div class="detail-header">
            <div class="detail-info">
                <h3>{prog_name}</h3>
                <p class="meta">{metrics['degree_level']} | Account Group: {prog_info['account_group']} | 
                    <a href="{prog_info['url']}" target="_blank">Landing Page &rarr;</a></p>
            </div>
        </div>

        <div class="kpi-grid">
            <div class="kpi">
                <div class="value">{metrics['leads']:,}</div>
                <div class="label">Total Leads (6mo)</div>
            </div>
            <div class="kpi">
                <div class="value">{metrics['apps_started']:,}</div>
                <div class="label">Apps Started ({metrics['app_start_rate']:.1f}%)</div>
            </div>
            <div class="kpi">
                <div class="value">{metrics['decisions']:,}</div>
                <div class="label">Decisions ({metrics['decision_rate']:.1f}%)</div>
            </div>
            <div class="kpi">
                <div class="value">{metrics['new_enrollments']:,}</div>
                <div class="label">Enrollments ({metrics['enrollment_rate']:.1f}%)</div>
            </div>
        </div>

        <h4 style="margin-bottom: 1rem; color: var(--uagc-dark);">Monthly Trend</h4>
        <table class="trend-table">
            <thead>
                <tr>
                    <th>Month</th>
                    <th>Leads</th>
                    <th>Apps Started</th>
                    <th>Decisions</th>
                    <th>New Enrollments</th>
                    <th>App %</th>
                    <th>Dec %</th>
                </tr>
            </thead>
            <tbody>
"""
    for m in months:
        app_pct = (m['apps_started'] / m['leads'] * 100) if m['leads'] else 0
        dec_pct = (m['decisions'] / m['leads'] * 100) if m['leads'] else 0
        html += f"""                <tr>
                    <td>{m['month']}</td>
                    <td>{m['leads']:,}</td>
                    <td>{m['apps_started']:,}</td>
                    <td>{m['decisions']:,}</td>
                    <td>{m['new_enrollments']:,}</td>
                    <td>{app_pct:.1f}%</td>
                    <td>{dec_pct:.1f}%</td>
                </tr>
"""
    
    html += """            </tbody>
        </table>

        <h4 style="margin: 1.5rem 0 0.5rem; color: var(--uagc-dark);">Lead Volume (Monthly)</h4>
"""
    for m in months:
        bar_width = int((m['leads'] / max_leads) * 100)
        html += f"""        <div class="funnel-bar">
            <span class="bar-label">{m['month']}</span>
            <div class="bar" style="width: {bar_width}%"></div>
            <span style="font-size:0.8rem">{m['leads']:,}</span>
        </div>
"""

    html += f"""
        <h4 style="margin: 1.5rem 0 0.5rem; color: var(--uagc-dark);">Landing Page Screenshot</h4>
        <div class="screenshot-container">
"""
    if prog_info['screenshot']:
        html += f'            <img src="data:image/png;base64,{prog_info["screenshot"]}" alt="{prog_name} landing page">\n'
    else:
        html += f'            <p style="color: var(--muted);">Screenshot not available</p>\n'
    
    html += """        </div>
    </div>

"""

html += """</div>
</body>
</html>"""

output_path = 'C:/Users/kseaman/Downloads/Cursor/program_report_poc.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Report generated: {output_path}")
print(f"File size: {os.path.getsize(output_path) / 1024:.0f} KB")
