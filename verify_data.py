import json
d = json.load(open('C:/Users/kseaman/Downloads/Cursor/program_data_full.json'))
print(f"Programs: {len(d['programs'])}")
print(f"Monthly keys: {len(d['monthly'])}")
print(f"Funnel keys: {len(d['funnel'])}")
p = d['programs'][0]
print(f"Top program: {p['program_name']} - CY:{p['leads']:,} PY:{p['py_leads']:,}")
