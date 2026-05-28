import zipfile
import xml.etree.ElementTree as ET
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

xlsx_path = r'c:\Users\kseaman\OneDrive - UAGC\General - Performance Marketing\Performance Marketing\Reporting Templates\MonthlyReporting\2026 - 04\Channel CPE Master - April.xlsx'

with zipfile.ZipFile(xlsx_path, 'r') as z:
    # Read shared strings
    ss_xml = z.read('xl/sharedStrings.xml')
    ss_root = ET.fromstring(ss_xml)
    shared_strings = []
    for si in ss_root.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
        text_parts = []
        for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
            if t.text:
                text_parts.append(t.text)
        shared_strings.append(''.join(text_parts))
    
    # Get sheet name to file mapping
    rels_xml = z.read('xl/_rels/workbook.xml.rels')
    rels_root = ET.fromstring(rels_xml)
    rid_to_file = {}
    for rel in rels_root:
        rid = rel.attrib.get('Id', '')
        target = rel.attrib.get('Target', '')
        rid_to_file[rid] = target
    
    wb_xml = z.read('xl/workbook.xml')
    wb_root = ET.fromstring(wb_xml)
    sheets_info = []
    for s in wb_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'):
        name = s.attrib.get('name')
        rid = s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        file_path = rid_to_file.get(rid, '')
        sheets_info.append((name, f'xl/{file_path}'))
    
    # Read channel detail sheets
    key_sheets = ['Brand', 'Nonbrand', 'AffiliateSearch', 'Media', 'Forecast Month', 'Fraud']
    
    for sheet_name in key_sheets:
        match = [(n, f) for n, f in sheets_info if n == sheet_name]
        if not match:
            print(f"=== Sheet '{sheet_name}' NOT FOUND ===\n")
            continue
        
        name, file_path = match[0]
        if file_path not in z.namelist():
            print(f"=== Sheet '{sheet_name}' file not in archive ===\n")
            continue
            
        print(f"=== Sheet: '{sheet_name}' ===")
        sheet_xml = z.read(file_path)
        sheet_root = ET.fromstring(sheet_xml)
        
        sheet_data = sheet_root.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData')
        if sheet_data is None:
            print("  (no sheetData)\n")
            continue
        
        rows = list(sheet_data.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'))
        print(f"  Total rows: {len(rows)}")
        
        for row in rows[:8]:
            row_num = row.attrib.get('r', '?')
            cells = []
            for cell in row.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                ref = cell.attrib.get('r', '')
                cell_type = cell.attrib.get('t', '')
                val_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                val = val_elem.text if val_elem is not None else ''
                
                if cell_type == 's' and val:
                    idx = int(val)
                    if idx < len(shared_strings):
                        val = shared_strings[idx][:40]
                
                if val:
                    cells.append(f"{ref}={val}")
            
            if cells:
                print(f"  Row {row_num}: {cells[:15]}")
        
        print()
    
    # Now try to extract Power Query M code from customXml
    print("=== Attempting Power Query extraction ===")
    for i in range(1, 5):
        fname = f'customXml/item{i}.xml'
        if fname in z.namelist():
            raw = z.read(fname)
            # Power Query DataMashup is stored as base64 in some cases
            # or as a binary blob. Let's check what we have
            try:
                text = raw.decode('utf-8', errors='replace')
                if 'DataMashup' in text:
                    print(f"  {fname}: Contains DataMashup (binary Power Query package)")
                    # The M code is embedded in a binary format inside the XML
                    # Let's look for readable M code patterns
                    import re
                    # Find anything that looks like M code
                    m_patterns = re.findall(r'(let\s+.*?in\s+\w+)', text, re.DOTALL | re.IGNORECASE)
                    if m_patterns:
                        for mp in m_patterns[:3]:
                            print(f"    M code found: {mp[:500]}")
                    else:
                        # Try to find Source = patterns
                        src_patterns = re.findall(r'Source\s*=.*?(?=\n)', text)
                        if src_patterns:
                            for sp in src_patterns[:5]:
                                print(f"    Source pattern: {sp[:200]}")
                        else:
                            # Look for SQL patterns
                            sql_patterns = re.findall(r'(?:SELECT|FROM|WHERE).*?(?=\x00|\n)', text, re.IGNORECASE)
                            if sql_patterns:
                                for sp in sql_patterns[:5]:
                                    print(f"    SQL found: {sp[:200]}")
                            else:
                                # Just dump any readable strings > 20 chars
                                readable = re.findall(r'[\x20-\x7e]{20,}', text)
                                print(f"    Readable strings ({len(readable)} found):")
                                for r_str in readable[:10]:
                                    print(f"      {r_str[:150]}")
            except Exception as e:
                print(f"  {fname}: Error - {e}")
    print()
