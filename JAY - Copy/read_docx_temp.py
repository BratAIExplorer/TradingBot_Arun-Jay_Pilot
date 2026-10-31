import zipfile
import xml.etree.ElementTree as ET
import sys

def get_docx_text(path):
    try:
        with zipfile.ZipFile(path) as document:
            xml_content = document.read('word/document.xml')
        
        tree = ET.fromstring(xml_content)
        
        namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        text_parts = []
        
        for p in tree.iterfind('.//w:p', namespace):
            texts = [node.text for node in p.iterfind('.//w:t', namespace) if node.text]
            if texts:
                text_parts.append(''.join(texts))
                
        return '\n'.join(text_parts)
    except Exception as e:
        return f"Error reading docx: {str(e)}"

if __name__ == "__main__":
    path = r"c:\Users\user\OneDrive\Documents\STock Trading\Arun-BOTProject\JAY - Copy\Set of conditions.docx"
    print(get_docx_text(path))
