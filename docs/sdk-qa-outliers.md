# Program outlier QA (baseline)

**Status: WARN** — three buckets need program dimension cleanup before publishing segment-level reports.

Validated against `advertising-data-mart.inquiries.vw_lead_extract_details` (last 30 days, `America/New_York`).

| Outlier key | BQ leads (30d) | Date range | Finding | Recommendation |
|-------------|----------------|------------|---------|----------------|
| `program_id` NULL | 1,521 | 2026-04-21 → 2026-05-21 | Matches `qa_outlier_programs.json`; large unattributed volume | Fix upstream program mapping in extract; exclude or label "Unknown program" in report matrix |
| `001Do00000ScUy6IAF` | 128 | 2026-04-21 → 2026-05-20 | Salesforce ID present but `program_name` null in file | Join to program dimension; confirm ID is valid active program |
| `Sociology` | 1 | 2026-05-07 | Text label used as `program_id` | Normalize to canonical program_id; likely bad ingest |

## SQL used

```sql
SELECT
  COALESCE(CAST(program_id AS STRING), 'NULL') AS program_id,
  COUNT(*) AS leads,
  MIN(inquiry_date) AS earliest_lead,
  MAX(inquiry_date) AS latest_lead
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= DATE_SUB(CURRENT_DATE('America/New_York'), INTERVAL 30 DAY)
  AND (
    program_id IS NULL
    OR program_name IS NULL
    OR program_id = '001Do00000ScUy6IAF'
    OR program_id = 'Sociology'
  )
GROUP BY 1
ORDER BY leads DESC;
```

---

*This file is the target output for `npm run qa:outliers`. Re-run after setting `CURSOR_API_KEY` so the SDK agent refreshes it with tool-call audit trail.*
