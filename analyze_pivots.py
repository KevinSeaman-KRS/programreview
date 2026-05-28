import zipfile
import xml.etree.ElementTree as ET

xlsx_path = r'c:\Users\kseaman\OneDrive - UAGC\General - Performance Marketing\Performance Marketing\Reporting Templates\MonthlyReporting\2026 - 04\Channel CPE Master - April.xlsx'

with zipfile.ZipFile(xlsx_path, 'r') as z:
    # Read pivot cache definitions to understand data sources
    print("=== Pivot Cache Definitions ===")
    for i in range(1, 11):
        fname = f'xl/pivotCache/pivotCacheDefinition{i}.xml'
        if fname in z.namelist():
            xml_data = z.read(fname)
            root = ET.fromstring(xml_data)
            # Get cache source info
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            cache_source = root.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}cacheSource')
            if cache_source is not None:
                src_type = cache_source.attrib.get('type', 'unknown')
                print(f"\n  PivotCache {i}: type={src_type}")
                # Worksheet source
                ws_src = cache_source.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}worksheetSource')
                if ws_src is not None:
                    print(f"    worksheet source: {dict(ws_src.attrib)}")
                # Connection-based
                conn_id = cache_source.attrib.get('connectionId')
                if conn_id:
                    print(f"    connectionId: {conn_id}")
            
            # Get field names from cache fields
            fields = root.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}cacheFields')
            if fields is not None:
                field_names = []
                for f in fields:
                    name = f.attrib.get('name', '')
                    field_names.append(name)
                print(f"    fields ({len(field_names)}): {field_names[:20]}")
                if len(field_names) > 20:
                    print(f"      ... and {len(field_names) - 20} more")
    
    print("\n\n=== Power Query (customXml) ===")
    for i in range(1, 5):
        fname = f'customXml/item{i}.xml'
        if fname in z.namelist():
            xml_data = z.read(fname)
            # Check if it's power query related
            text = xml_data.decode('utf-8', errors='replace')
            if 'DataMashup' in text or 'powerquery' in text.lower() or 'Section1' in text:
                print(f"\n  {fname}: Contains Power Query / DataMashup")
                # Try to find M code
                if 'Section1' in text:
                    # Extract readable portions
                    start = text.find('Section1')
                    if start > 0:
                        snippet = text[start:start+2000]
                        print(f"    M code snippet: {snippet[:1500]}")
            elif len(text) < 500:
                print(f"\n  {fname}: {text[:300]}")
            else:
                print(f"\n  {fname}: ({len(text)} chars, first 200: {text[:200]})")
