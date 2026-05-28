"""
Program Performance Report - Filtered to Master Spreadsheet programs only.
Also generates QA report for leads NOT in the master list.
"""
from google.cloud import bigquery
import json

client = bigquery.Client(project='advertising-data-mart')

MASTER_PROGRAM_IDS = [
    '001Do00000ScUyCIAV',  # AA in Business
    '001Do00000ScUzUIAV',  # AA in Early Childhood Education
    '001Do00000ScUyvIAF',  # AA in Military Studies
    '001Do00000ScUyDIAV',  # AA in Organizational Management
    '001Do00000ScUyPIAV',  # BA in Accounting
    '001Do00000ScUzGIAV',  # BA in Applied Behavioral Science
    '001Do00000ScUyQIAV',  # BA in Business Administration
    '001Do00000ScUyEIAV',  # BA in Business Economics
    '001Do00000ScUzHIAV',  # BA in Business Information Systems
    '001Do00000ScUyRIAV',  # BA in Business Leadership
    '001Do00000ScUzdIAF',  # BA in Child Development
    '001Do00000ScUysIAF',  # BA in Communication Studies
    '001Do00000ScUzeIAF',  # BA in Early Childhood Development w/ Differentiated Instruction
    '001Do00000ScUzfIAF',  # BA in Early Childhood Education
    '001Do00000ScUzgIAF',  # BA in Early Childhood Education Administration
    '001Do00000ScUzhIAF',  # BA in Education Studies
    '001Do00000ScUySIAV',  # BA in Finance
    '001Do00000ScUzEIAV',  # BA in Health & Human Services
    '001Do00000ScUyeIAF',  # BA in Health and Wellness
    '001Do00000ScUybIAF',  # BA in Health Care Administration
    '001Do00000ScUz6IAF',  # BA in Homeland Security and Emergency Management
    '001Do00000ScUyXIAV',  # BA in Human Resources Management
    '001Do00000ScUzZIAV',  # BA in Instructional Design
    '001Do00000ScUyqIAF',  # BA in Liberal Arts
    '001Do00000ScUyTIAV',  # BA in Marketing
    '001Do00000ScUyUIAV',  # BA in Operations Management & Analysis
    '001Do00000ScUyVIAV',  # BA in Organizational Management
    '001Do00000ScUyWIAV',  # BA in Project Management
    '001Do00000ScUzFIAV',  # BA in Psychology
    '001Do00000ScUz7IAF',  # BA in Social and Criminal Justice
    '001Do00000ScUyzIAF',  # BA in Social Science
    '001Do00000ScUzCIAV',  # BA in Sociology
    '001Do00000ScUyNIAV',  # BA in Supply Chain Management
    '001Do00000ScUzIIAV',  # BS in Computer Software Technology
    '001Do00000ScUzJIAV',  # BS in Cyber & Data Security Technology
    '001Do00000ScUyaIAF',  # BS in Health Information Management
    '001Do00000ScUzKIAV',  # BS in Information Technology
    '001Do00000ScUymIAF',  # BS in Nursing
    '001Vr00000YtotRIAR',  # DPS in Organizational Leadership
    '001Do00000ScUzbIAF',  # MA in Early Childhood Education Leadership
    '001Do00000ScUzcIAF',  # MA in Education
    '001Do00000ScUynIAF',  # MA in Health Care Administration
    '001Do00000ScUzAIAV',  # MA in Human Services
    '001Do00000ScUy8IAF',  # MA in Organizational Management
    '001Do00000ScUz9IAF',  # MA in Psychology
    '001Do00000ScUzSIAV',  # MA in Special Education
    '001Do00000ScUzTIAV',  # MA in Teaching and Learning with Technology
    '001Do00000ScUyZIAV',  # Master of Accountancy
    '001Do00000ScUy9IAF',  # Master of Business Administration
    '001Do00000ScUyAIAV',  # Master of Human Resource Management
    '001Do00000ScUzMIAV',  # Master of Information Systems Management
    '001Do00000ScUylIAF',  # Master of Public Health
    '001Vr00000t9K7vIAE',  # MPS in Leadership
    '001Do00000ScUz8IAF',  # MS in Criminal Justice
    '001Do00000ScUyBIAV',  # MS in Finance
    '001Do00000ScUykIAF',  # MS in Health Informatics and Analytics
    '001Do00000ScUzQIAV',  # MS in Instructional Design and Technology
    '001Do00000ScUzNIAV',  # MS in Technology Management
    '001Do00000ScUzOIAV',  # Post Baccalaureate Teaching Certificate - Elementary Education
    '001Do00000YZZzVIAX',  # Undecided - Bachelors
    '001Do00000YZZxZIAX',  # Undecided - Business
    '001Do00000YZZxjIAH',  # Undecided - Criminal Justice
    '001Do00000YZZyXIAX',  # Undecided - Education
    '001Do00000YZZyYIAX',  # Undecided - Health Care
    '001Do00000YZZymIAH',  # Undecided - Information Technology
    '001Do00000YZZz6IAH',  # Undecided - Liberal Arts
    '001Do00000YZZz7IAH',  # Undecided - Masters
    '001Do00000YZZzGIAX',  # Undecided - Social & Behavioral Science
    '001Do00000YZZzHIAX',  # Undecided - Undecided
]

print(f"Master list: {len(MASTER_PROGRAM_IDS)} programs")

id_list_sql = ", ".join([f"'{pid}'" for pid in MASTER_PROGRAM_IDS])

# === PART 1: Filtered matrix (6 months) ===
print("\n" + "=" * 80)
print("PART 1: Program Matrix (filtered to master list, last 6 months)")
print("=" * 80)

query_matrix = f"""
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
  AND program_id IN ({id_list_sql})
GROUP BY program_id, program_name, degree_level
ORDER BY leads DESC
"""

results = client.query(query_matrix).result()
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

print(f"\nMatched {len(programs)} of {len(MASTER_PROGRAM_IDS)} master programs in lead data")
print(f"Total leads (6mo): {sum(p['leads'] for p in programs):,}")
print()

print(f"{'#':<3} {'Program Name':<55} {'Level':<15} {'Leads':>7} {'Apps':>7} {'Dec':>7} {'Enrl':>7} {'App%':>6} {'Dec%':>6}")
print("-" * 115)
for i, p in enumerate(programs, 1):
    print(f"{i:<3} {(p['program_name'] or '')[:54]:<55} {(p['degree_level'] or ''):<15} {p['leads']:>7} {p['apps_started']:>7} {p['decisions']:>7} {p['new_enrollments']:>7} {p['app_start_rate']:>5.1f}% {p['decision_rate']:>5.1f}%")

with open('C:/Users/kseaman/Downloads/Cursor/program_metrics_filtered.json', 'w') as f:
    json.dump(programs, f, indent=2)

# === PART 2: QA - leads in last 30 days NOT in master list ===
print("\n\n" + "=" * 80)
print("PART 2: QA REPORT - Leads in last 30 days NOT in master program list")
print("=" * 80)

query_qa = f"""
SELECT
    program_id,
    program_name,
    degree_level,
    COUNT(*) AS leads,
    MIN(inquiry_date) AS earliest_lead,
    MAX(inquiry_date) AS latest_lead
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= DATE_SUB(CURRENT_DATE('America/New_York'), INTERVAL 30 DAY)
  AND (program_id NOT IN ({id_list_sql}) OR program_id IS NULL)
GROUP BY program_id, program_name, degree_level
ORDER BY leads DESC
"""

results_qa = client.query(query_qa).result()
qa_rows = []
for row in results_qa:
    qa_rows.append({
        'program_id': row.program_id,
        'program_name': row.program_name,
        'degree_level': row.degree_level,
        'leads': row.leads,
        'earliest_lead': str(row.earliest_lead),
        'latest_lead': str(row.latest_lead),
    })

total_outlier_leads = sum(r['leads'] for r in qa_rows)
print(f"\nFound {len(qa_rows)} programs outside master list")
print(f"Total outlier leads (last 30 days): {total_outlier_leads:,}")
print()

if qa_rows:
    print(f"{'Program ID':<22} {'Program Name':<50} {'Level':<15} {'Leads':>7} {'Earliest':<12} {'Latest':<12}")
    print("-" * 120)
    for r in qa_rows:
        pid = r['program_id'] or '(NULL)'
        name = r['program_name'] or '(NULL)'
        level = r['degree_level'] or ''
        print(f"{pid[:21]:<22} {name[:49]:<50} {level:<15} {r['leads']:>7} {r['earliest_lead']:<12} {r['latest_lead']:<12}")
else:
    print("No outlier leads found! All recent leads map to master program list.")

with open('C:/Users/kseaman/Downloads/Cursor/qa_outlier_programs.json', 'w') as f:
    json.dump(qa_rows, f, indent=2)

print(f"\nSaved filtered metrics to: program_metrics_filtered.json")
print(f"Saved QA report to: qa_outlier_programs.json")
