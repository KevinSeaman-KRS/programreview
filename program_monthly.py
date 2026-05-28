"""
Pull monthly trended data for POC programs.
"""
from google.cloud import bigquery
import json

client = bigquery.Client(project='advertising-data-mart')

query = """
SELECT
    program_id,
    program_name,
    FORMAT_DATE('%Y-%m', inquiry_date) AS month,
    COUNT(*) AS leads,
    SUM(is_app_started) AS apps_started,
    SUM(is_appin) AS decisions,
    SUM(IFNULL(is_new_enrollment, 0)) AS new_enrollments
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= '2025-12-20'
  AND program_name IN ('BA in Business Administration', 'Master of Business Administration')
GROUP BY program_id, program_name, month
ORDER BY program_name, month
"""

print("Querying monthly trend data...")
results = client.query(query).result()

monthly = {}
for row in results:
    key = row.program_name
    if key not in monthly:
        monthly[key] = []
    monthly[key].append({
        'month': row.month,
        'leads': row.leads,
        'apps_started': row.apps_started,
        'decisions': row.decisions,
        'new_enrollments': row.new_enrollments
    })

for prog, data in monthly.items():
    print(f"\n{prog}:")
    print(f"  {'Month':<10} {'Leads':>7} {'Apps':>7} {'Dec':>7} {'Enrl':>7}")
    for d in data:
        print(f"  {d['month']:<10} {d['leads']:>7} {d['apps_started']:>7} {d['decisions']:>7} {d['new_enrollments']:>7}")

with open('C:/Users/kseaman/Downloads/Cursor/program_monthly.json', 'w') as f:
    json.dump(monthly, f, indent=2)
print("\nSaved to program_monthly.json")
