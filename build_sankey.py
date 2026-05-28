"""Inject real data into the Sankey HTML template."""
import json

with open('C:/Users/kseaman/Downloads/Cursor/program_data_full.json') as f:
    data = json.load(f)

with open('C:/Users/kseaman/Downloads/Cursor/sankey_poc.html') as f:
    html = f.read()

js_data = json.dumps({
    'programs': data['programs'],
    'funnel': data['funnel']
})

html = html.replace('PROGRAM_DATA_PLACEHOLDER', js_data)

with open('C:/Users/kseaman/Downloads/Cursor/sankey_poc.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Sankey HTML ready with live data")
