import zipfile
import xml.etree.ElementTree as ET
import os

xlsx_path = r'c:\Users\kseaman\OneDrive - UAGC\General - Performance Marketing\Performance Marketing\Reporting Templates\MonthlyReporting\2026 - 04\Channel CPE Master - April.xlsx'

with zipfile.ZipFile(xlsx_path, 'r') as z:
    # List all files in the xlsx
    print("=== Files in XLSX archive ===")
    for name in sorted(z.namelist()):
        print(f"  {name}")
    print()
    
    # Read workbook.xml to get sheet names
    print("=== Sheet Names ===")
    wb_xml = z.read('xl/workbook.xml')
    root = ET.fromstring(wb_xml)
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    sheets = root.findall('.//main:sheet', ns)
    for s in sheets:
        print(f"  {s.attrib.get('name')} (sheetId={s.attrib.get('sheetId')})")
    print()
    
    # Check for data connections
    if 'xl/connections.xml' in z.namelist():
        print("=== Data Connections ===")
        conn_xml = z.read('xl/connections.xml')
        conn_root = ET.fromstring(conn_xml)
        # Print raw connection info
        for conn in conn_root:
            attribs = dict(conn.attrib)
            print(f"  Connection: name={attribs.get('name', 'unknown')}, type={attribs.get('type', 'unknown')}")
            for child in conn:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                print(f"    {tag}: {dict(child.attrib)}")
                if child.text and child.text.strip():
                    print(f"      text: {child.text[:200]}")
                for grandchild in child:
                    gtag = grandchild.tag.split('}')[-1] if '}' in grandchild.tag else grandchild.tag
                    print(f"      {gtag}: {dict(grandchild.attrib)}")
                    if grandchild.text and grandchild.text.strip():
                        print(f"        text: {grandchild.text[:300]}")
        print()
    
    # Check for queries
    query_files = [f for f in z.namelist() if 'query' in f.lower() or 'customXml' in f]
    if query_files:
        print("=== Query-related files ===")
        for qf in query_files:
            print(f"  {qf}")
