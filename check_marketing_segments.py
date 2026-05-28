"""Check marketing_segment_rollup distribution for Sankey inflow design."""
from google.cloud import bigquery

client = bigquery.Client(project='advertising-data-mart')

query = """
SELECT
    marketing_segment_rollup,
    COUNT(*) AS leads,
    SUM(is_app_started) AS app_starts,
    SUM(IFNULL(is_new_enrollment, 0)) AS enrollments
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= DATE_SUB(CURRENT_DATE('America/New_York'), INTERVAL 12 MONTH)
GROUP BY marketing_segment_rollup
ORDER BY leads DESC
"""

print("Marketing segment rollup (12 months, all programs):\n")
results = client.query(query).result()
rows = list(results)
for row in rows:
    seg = row.marketing_segment_rollup or '(NULL)'
    print(f"  {seg:<35} {row.leads:>8,} leads  |  {row.enrollments:>5,} enrl")

print(f"\nTotal segments: {len(rows)}")

# Same for BA in Business Administration
query2 = """
SELECT
    marketing_segment_rollup,
    COUNT(*) AS leads
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= DATE_SUB(CURRENT_DATE('America/New_York'), INTERVAL 12 MONTH)
  AND program_id = '001Do00000ScUyQIAV'
GROUP BY marketing_segment_rollup
ORDER BY leads DESC
"""

print("\n\nBA in Business Administration:\n")
for row in client.query(query2).result():
    seg = row.marketing_segment_rollup or '(NULL)'
    print(f"  {seg:<35} {row.leads:>8,} leads")
