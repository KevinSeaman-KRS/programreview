"""
Legacy POC — use pull_program_demographics.py for all 59 programs via program_srm_bridge.
"""
import pymssql
import json

conn = pymssql.connect(server='prodedlsql02', database='marketingsandbox')
cursor = conn.cursor()

query = """
SELECT systudentid, degreelevel, majorname,
       race, gender, pell, maritalstatus, transferstatus, 
       age_at_matric, lineofbusiness, minority, state
FROM [dbo].[StudentRevenueMaster]
WHERE MATRICDATE > '2025-04-01'
"""

print("Querying StudentRevenueMaster...")
cursor.execute(query)
columns = [desc[0] for desc in cursor.description]
rows = []
for row in cursor.fetchall():
    rows.append(dict(zip(columns, row)))

conn.close()
print(f"Retrieved {len(rows):,} enrolled students")

# Get top majors
from collections import Counter
major_counts = Counter(r['majorname'] for r in rows if r['majorname'])
print(f"\nUnique majors: {len(major_counts)}")
print("\nTop 15 majors by enrollment:")
for major, count in major_counts.most_common(15):
    print(f"  {count:>5}  {major}")

# Profile function
def profile(subset, label):
    n = len(subset)
    if n == 0:
        return None
    
    def dist(field):
        c = Counter(r[field] for r in subset if r[field] is not None)
        return {k: round(v/n*100, 1) for k, v in c.most_common(10)}
    
    ages = [r['age_at_matric'] for r in subset if r['age_at_matric'] is not None]
    
    return {
        'label': label,
        'count': n,
        'gender': dist('gender'),
        'race': dist('race'),
        'minority': dist('minority'),
        'pell': dist('pell'),
        'maritalstatus': dist('maritalstatus'),
        'transferstatus': dist('transferstatus'),
        'lineofbusiness': dist('lineofbusiness'),
        'degreelevel': dist('degreelevel'),
        'age_median': sorted(ages)[len(ages)//2] if ages else None,
        'age_mean': round(sum(ages)/len(ages), 1) if ages else None,
        'age_under25': round(sum(1 for a in ages if a < 25)/len(ages)*100, 1) if ages else None,
        'age_25to34': round(sum(1 for a in ages if 25 <= a < 35)/len(ages)*100, 1) if ages else None,
        'age_35to44': round(sum(1 for a in ages if 35 <= a < 45)/len(ages)*100, 1) if ages else None,
        'age_45plus': round(sum(1 for a in ages if a >= 45)/len(ages)*100, 1) if ages else None,
        'top_states': dist('state'),
    }

# Profile: All students
print("\n" + "="*70)
print("DEMOGRAPHIC PROFILE: ALL ENROLLED STUDENTS")
print("="*70)
all_profile = profile(rows, "All Enrolled Students")
for k, v in all_profile.items():
    if k in ('label', 'count'):
        print(f"  {k}: {v}")
    else:
        print(f"  {k}: {v}")

# Profile: BA in Business Administration (likely "Business Administration" or similar)
baba_rows = [r for r in rows if r['majorname'] and 'Business Administration' in r['majorname'] and r['degreelevel'] and 'Bach' in r['degreelevel']]
print(f"\n{'='*70}")
print(f"DEMOGRAPHIC PROFILE: BA in Business Administration ({len(baba_rows)} students)")
print("="*70)
baba_profile = profile(baba_rows, "BA in Business Administration")
if baba_profile:
    for k, v in baba_profile.items():
        print(f"  {k}: {v}")

# Profile: MBA
mba_rows = [r for r in rows if r['majorname'] and 'Business Administration' in r['majorname'] and r['degreelevel'] and 'Mast' in r['degreelevel']]
print(f"\n{'='*70}")
print(f"DEMOGRAPHIC PROFILE: MBA ({len(mba_rows)} students)")
print("="*70)
mba_profile = profile(mba_rows, "Master of Business Administration")
if mba_profile:
    for k, v in mba_profile.items():
        print(f"  {k}: {v}")

# Profile: BA in Psychology
psych_rows = [r for r in rows if r['majorname'] and 'Psychology' in r['majorname'] and r['degreelevel'] and 'Bach' in r['degreelevel']]
print(f"\n{'='*70}")
print(f"DEMOGRAPHIC PROFILE: BA in Psychology ({len(psych_rows)} students)")
print("="*70)
psych_profile = profile(psych_rows, "BA in Psychology")
if psych_profile:
    for k, v in psych_profile.items():
        print(f"  {k}: {v}")

# Save all profiles
output = {
    'all': all_profile,
    'baba': baba_profile,
    'mba': mba_profile,
    'psychology': psych_profile,
    'major_counts': dict(major_counts.most_common(50)),
}
with open('C:/Users/kseaman/Downloads/Cursor/demographics.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\nSaved to demographics.json")
