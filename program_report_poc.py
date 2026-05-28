"""
Program Performance Report - Proof of Concept
Generates a summary matrix + detail pages for a few sample programs.
"""
from google.cloud import bigquery
import json
import os

client = bigquery.Client(project='advertising-data-mart')

# Pull 6-month metrics by inquiry program
query = """
SELECT
    program_id,
    program_name,
    degree_level,
    COUNT(*) AS leads,
    SUM(is_app_started) AS apps_started,
    SUM(is_appin) AS decisions,
    SUM(IFNULL(is_new_enrollment, 0)) AS new_enrollments,
    SAFE_DIVIDE(SUM(is_app_started), COUNT(*)) AS app_start_rate,
    SAFE_DIVIDE(SUM(is_appin), COUNT(*)) AS decision_rate,
    SAFE_DIVIDE(SUM(IFNULL(is_new_enrollment, 0)), COUNT(*)) AS enrollment_rate
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= '2025-12-20'
GROUP BY program_id, program_name, degree_level
ORDER BY leads DESC
"""

print("Querying BigQuery for 6-month program metrics...")
results = client.query(query).result()

programs = []
for row in results:
    programs.append({
        'program_id': row.program_id,
        'program_name': row.program_name,
        'degree_level': row.degree_level,
        'leads': row.leads,
        'apps_started': row.apps_started,
        'decisions': row.decisions,
        'new_enrollments': row.new_enrollments,
        'app_start_rate': round(row.app_start_rate * 100, 1) if row.app_start_rate else 0,
        'decision_rate': round(row.decision_rate * 100, 1) if row.decision_rate else 0,
        'enrollment_rate': round(row.enrollment_rate * 100, 1) if row.enrollment_rate else 0,
    })

print(f"Retrieved {len(programs)} programs")
print()

# Print summary matrix (top 10 for POC)
print("=" * 100)
print("SUMMARY MATRIX (all programs, sorted by leads)")
print("=" * 100)
print(f"{'Program Name':<55} {'Level':<15} {'Leads':>7} {'Apps':>7} {'Dec':>7} {'Enrl':>7} {'App%':>6} {'Dec%':>6}")
print("-" * 100)
for p in programs:
    print(f"{(p['program_name'] or 'NULL')[:54]:<55} {(p['degree_level'] or ''):<15} {p['leads']:>7} {p['apps_started']:>7} {p['decisions']:>7} {p['new_enrollments']:>7} {p['app_start_rate']:>5.1f}% {p['decision_rate']:>5.1f}%")

print()
print(f"Total programs: {len(programs)}")
print(f"Total leads: {sum(p['leads'] for p in programs)}")

# Save as JSON for later use
with open('C:/Users/kseaman/Downloads/Cursor/program_metrics.json', 'w') as f:
    json.dump(programs, f, indent=2)
print("\nSaved to program_metrics.json")
