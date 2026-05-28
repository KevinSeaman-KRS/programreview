import json
with open('C:/Users/kseaman/Downloads/Cursor/program_data_full.json') as f:
    data = json.load(f)
pid = '001Do00000ScUyQIAV'
f = data['funnel'][pid]
p = next(x for x in data['programs'] if x['program_id'] == pid)
print(f"{p['program_name']}:")
print(f"  Inquiries:   {f['inquiries']:,}")
print(f"  App Starts:  {f['app_starts']:,}")
print(f"  App Submits: {f['app_submits']:,}")
print(f"  Decisions:   {f['decisions']:,}")
print(f"  Enrollments: {f['enrollments']:,}")
