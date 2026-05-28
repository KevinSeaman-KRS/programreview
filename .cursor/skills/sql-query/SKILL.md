---
name: sql-query
description: Query marketing lead and enrollment data from SQL Server and BigQuery. Use when the user asks about leads, inquiries, applications, enrollments, funnel metrics, program performance, channel performance, or any marketing analytics question involving data retrieval.
---

# SQL Query Skill

## Data Sources

**Preferred source: BigQuery** (use unless SQL Server is specifically requested)

| Source | Connection | Primary Table |
|--------|-----------|---------------|
| BigQuery | project: `advertising-data-mart`, location: `US` | `advertising-data-mart.inquiries.vw_lead_extract_details` |
| SQL Server | server: `prodedlsql02`, database: `marketingsandbox`, Windows Auth | `dbo.vw_lead_extract_details` |

Both contain the same data (one row per inquiry). SQL Server refreshes late morning ET, then syncs to BigQuery after.

## Connection Patterns

### BigQuery (preferred)

```python
from google.cloud import bigquery
client = bigquery.Client(project='advertising-data-mart')
query = "SELECT ... FROM `advertising-data-mart.inquiries.vw_lead_extract_details` WHERE ..."
result = client.query(query).result()
```

Run via: `uvx --from mcp-server-bigquery --with google-cloud-bigquery python script.py`

### SQL Server

```python
import pymssql
conn = pymssql.connect(server='prodedlsql02', database='marketingsandbox')
cursor = conn.cursor()
cursor.execute("SELECT ... FROM dbo.vw_lead_extract_details WHERE ...")
```

Run via: `uvx --from microsoft_sql_server_mcp python script.py`

## Timezone Rule

BigQuery uses UTC by default. Always use `CURRENT_DATE('America/New_York')` or explicit dates to align with SQL Server and business expectations.

## Key Column Name Differences

| Concept | SQL Server | BigQuery |
|---------|-----------|----------|
| New enrollment | `is_lead_cube_new_enrollment` | `is_new_enrollment` |
| Final enrollment | `is_lead_cube_new_enrollment_final` | `is_new_enrollment_final` |
| Enrollment date | `lead_cube_new_enrollment_date` | `new_enrollment_date` |

All other columns share the same names.

## Funnel Stages (in order)

```
inquiry → new_lead → first_contacted → EA_contacted → warm_transfer →
portal_login → app_started → app_submitted → app_signed_and_submitted →
appin (decision) → registered → sit → new_enrollment → first_course_completed → course_2_completed
```

Each stage has:
- A flag column: `is_<stage>` (int, 0/1)
- A date column: `<stage>_date`
- Many have speed flags: `is_<stage>_7_days`, `is_<stage>_14_days`

## Key Metrics (the three everyone cares about)

| Metric | Column (BQ) | Column (SQL) | Meaning |
|--------|------------|--------------|---------|
| App Started | `is_app_started` | `is_app_started` | Started the online application |
| Decision/Appin | `is_appin` | `is_appin` | Received admissions decision (accepted) |
| New Enrollment | `is_new_enrollment` | `is_lead_cube_new_enrollment` | Matriculated — enrolled and started |

## About UAGC

UAGC = **University of Arizona Global Campus** — an online university offering 60 active degree programs plus 10 "Undecided" placeholder selections.

- **Website**: www.uagc.edu
- **Program landing pages**: www.uagc.edu/online-degrees/...
- **Program Master spreadsheet**: https://docs.google.com/spreadsheets/d/15_Dr_JYLcJSbjoNYFH-dqeAs2Q4P-MKjrmaoJzBI67c/edit?gid=1877267984

### Degree levels offered
| Level | Count | Examples |
|-------|-------|----------|
| Associates | 4 | AA in Business, AA in Early Childhood Education |
| Bachelors | 35 | BA in Business Administration, BS in Nursing, BS in Cyber & Data Security Technology |
| Masters | 19 | MBA, MA in Psychology, MS in Criminal Justice |
| Doctoral | 1 | DPS in Organizational Leadership |
| Post-Baccalaureate | 1 | Teaching Certificate - Elementary Education |

### Account groups (academic colleges)
Business, Education, Health Care, Criminal Justice, Social & Behavioral Science, Liberal Arts, Information Technology

### Program reference data
- `program_id` (a.k.a. `lesn_program_id`) links lead data to program details
- `dbo.vw_program` (SQL) or Program Master spreadsheet contain program attributes
- **`dbo.program_srm_bridge`** — maps 59 report `program_id` values to `StudentRevenueMaster` (`degreelevel`, `majorname`). Built by `scripts/build_program_bridge.py`; artifacts in `data/program_srm_bridge.csv`.

**Three naming layers (do not join on name alone):**

| Layer | Example fields | Example |
|-------|------------------|---------|
| Marketing / leads | `program_name` on `vw_lead_extract_details` | `BA in Business Administration` |
| Program master | `full_program_name` on `dbo.vw_program` | `Bachelor of Arts in Business Administration` |
| Student revenue | `degreelevel`, `majorname` on `dbo.StudentRevenueMaster` | `Bachelor`, `Business Administration` |

```sql
-- Demographics or revenue for a marketing program_id
SELECT b.program_id, b.lead_program_name, s.*
FROM dbo.StudentRevenueMaster s
INNER JOIN dbo.program_srm_bridge b
  ON s.degreelevel = b.srm_degreelevel AND s.majorname = b.srm_majorname
WHERE b.program_id = '001Do00000ScUyPIAV';
```

SRM `degreelevel` values: `Associate`, `Bachelor`, `Master`, `Doctorate`, `Graduate Certificate`, `NDS` (non-degree — no bridge row).

**Program report demographics:** `pull_program_demographics.py` → `program_demographics.json`; rendered on detail pages in `generate_full_report.py` (12-month matric window, indexed vs undergrad/grad baseline).
- The spreadsheet's "Web URL" column has program landing page URLs (not available in SQL)
- **Undecided programs** (10 rows, `is_enrolling=0`): prospects can select these on RFI forms but must choose an actual program at application stage

## Inquiry Program vs. Applied Program

The lead table tracks **two different program references**:

| Concept | Fields | Meaning |
|---------|--------|---------|
| **Inquiry program** | `program_id`, `degree_level`, `degree_type`, `program_name`, `program_code` | The program the prospect originally inquired about. May include "Undecided" selections. |
| **Applied program** | `applied_program_id`, `applied_degree_level`, `applied_degree_type`, `applied_program_name`, `applied_program_code`, `applied_area_of_interest` | The program on the actual application. Should NOT contain undecided values. |

**Key patterns:**
- Prospects often inquire about one program but apply/enroll in a different one — almost always within the same academic level.
- Cross-level changes (e.g., inquired Masters → enrolled Bachelors) are rare noise; ignore for analysis.
- When analyzing inquiry-to-application program migration, **filter to `is_app_submitted = 1`** to avoid the distraction of leads without an applied program.
- The undecided inquiry programs will "resolve" into actual programs at application stage.

### Undecided bucket (migration / program-flow reports)

For inquiry-side grouping in program migration views, collapse all undecided inquiry rows into one label **`Undecided`**. Applied/enrollment side never uses undecided.

```sql
CASE
  WHEN program_name LIKE 'Undecided%' THEN 'Undecided'
  ELSE program_name
END AS inquiry_program_bucket
```

There are 10 undecided inquiry `program_name` values (e.g. `Undecided - Criminal Justice`, `Undecided - Undecided`). Do not list them separately in top-N inflow tables — roll into `Undecided`, then rank top 3 non-undecided programs plus `Undecided` if it places in the top 3.

### Two enrollment metrics (do not conflate)

| Topic | Anchor | Flag | Denominator / grain |
|-------|--------|------|---------------------|
| **Program enrollments** | `applied_program_*` | `is_new_enrollment_final = 1` | Count final enrollments **in that applied program**; show where inquiry came from |
| **Leads / cohort** | `program_id` / inquiry program | `SUM(is_new_enrollment_final)` over 12-mo inquiry cohort | `enrollment_rate = final enrollments ÷ inquiry leads` (cohorted flow) |

Use **`is_new_enrollment_final`** for migration and program-flow views unless a report column explicitly requires provisional `is_new_enrollment`.

### Program flow (detail tab) — two blocks

**1. Program enrollments — where they came from** (`enrollment_view`)

Per **applied program** (anchor), final enrollments only:

| Inquiry program | Final enrollments | % | Applied (enrolled) program |

Rows: (1) same inquiry → same applied, (2) inflows — applied = anchor, top 5 inquiry buckets + Other, (3) outflows — inquiry = anchor, top 3 applied + Other.

**Summary strip:** enrollments in program, same-path, gained, lost, **net = gained − lost**, **net %** = net ÷ enrollments in program (and vs same-path base).

**2. Inquiry cohort — where leads enrolled** (`lead_cohort_view`)

Per **inquiry program** (anchor), 12-month inquiry leads:

| Inquiry program | Final enrollments | % | Applied (enrolled) program |

Summary: inquiry leads, final enrollments, **enrollment_rate_pct**, enrolled in this program vs elsewhere.

**Undecided bucket** on inquiry column only. Rules: same `degree_level` = `applied_degree_level`; exclude cross-level rows; `applied_program_id` required for enrollment_view enrollee rows.

## Jargon Dictionary

| Term | Meaning |
|------|---------|
| **Appin** / **Decision** | Admissions decision received (accepted) |
| **SIT** | Student "sat" for the first day of class |
| **EA** | Enrollment Advisor — the person who contacts leads |
| **RFI** | Request For Information — an inquiry form submission |
| **Warm transfer** | Live phone transfer to an EA |
| **First contacted** | First successful contact by an EA |
| **App signed and submitted** | Application fully signed and submitted for review |
| **LESN** | Lead/inquiry identifier prefix (e.g., `lesn_campaign_id`) |

## Lead Categorization Hierarchies

There are two primary hierarchies used to categorize leads:

### Hierarchy 1: Marketing Segment

A classification of the lead source at a broad strategic level.

| Level | Column(s) | Notes |
|-------|-----------|-------|
| Rollup (broadest) | `marketing_segment_rollup` | High-level grouping |
| Segment | `mars_segment` / `marketing_segment` / `mars_segment_legacy` | These are aliases for the same concept |

### Hierarchy 2: Channel (Campaign-based)

A more granular classification derived from `campaign_id`. Joins to `vw_campaign` in SQL Server for campaign metadata. These levels are editable metadata (some records need cleanup).

| Level | Column | Granularity |
|-------|--------|-------------|
| 1 (broadest) | `primary_channel_rollup` | Highest-level channel grouping |
| 2 | `channel_rollup` | |
| 3 | `Channel` | |
| 4 | `Sub_channel` | |
| 5 (most granular) | `vendor` | Specific partner/vendor |

**Joining campaigns**: `campaign_id` on the lead table joins to `vw_campaign` for the full channel metadata hierarchy.

## Common Dimensions for Grouping

- **Marketing Segment**: `marketing_segment_rollup` → `mars_segment`
- **Channel hierarchy**: `primary_channel_rollup` → `channel_rollup` → `channel` → `sub_channel` → `vendor` (from `vw_campaign` via `campaign_id`)
- **Program**: `program_name`, `degree_level` (Graduate/Undergraduate), `degree_type` (Masters/Bachelors/Associates), `area_of_interest`
- **Time**: `inquiry_date`, `inquiry_year`, `inquiry_month`, `yyyy_mm`, `week_starting_sun`
- **Geography**: `state_abbreviation`, `postal_code`
- **Demographics**: `is_military_affiliated`, `highest_level_of_education`, `employer`

## Example Queries

### Daily lead count with key metrics (BigQuery)
```sql
SELECT
    inquiry_date,
    COUNT(*) AS leads,
    SUM(is_app_started) AS apps_started,
    SUM(is_appin) AS decisions,
    SUM(IFNULL(is_new_enrollment, 0)) AS new_enrollments
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= DATE_SUB(CURRENT_DATE('America/New_York'), INTERVAL 7 DAY)
GROUP BY inquiry_date
ORDER BY inquiry_date
```

### Channel performance
```sql
SELECT
    business_channel,
    channel_rollup,
    COUNT(*) AS leads,
    SUM(is_app_started) AS apps_started,
    SAFE_DIVIDE(SUM(is_app_started), COUNT(*)) AS app_start_rate,
    SUM(is_appin) AS decisions,
    SAFE_DIVIDE(SUM(is_appin), COUNT(*)) AS decision_rate
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= DATE_SUB(CURRENT_DATE('America/New_York'), INTERVAL 30 DAY)
GROUP BY business_channel, channel_rollup
ORDER BY leads DESC
```

### Funnel conversion rates by program
```sql
SELECT
    degree_level,
    program_name,
    COUNT(*) AS leads,
    SAFE_DIVIDE(SUM(is_app_started), COUNT(*)) AS inq_to_app_rate,
    SAFE_DIVIDE(SUM(is_appin), SUM(is_app_started)) AS app_to_decision_rate,
    SAFE_DIVIDE(SUM(is_new_enrollment), SUM(is_appin)) AS decision_to_enroll_rate
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= DATE_SUB(CURRENT_DATE('America/New_York'), INTERVAL 90 DAY)
GROUP BY degree_level, program_name
HAVING leads >= 50
ORDER BY leads DESC
```
