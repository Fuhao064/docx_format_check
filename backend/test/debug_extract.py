"""Debug script to see what extractors actually output"""
import sys
import json
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from preparation.para_type import ParagraphManager

test_dir = Path(__file__).parent
doc_path = test_dir / "测试引擎.docx"

print("Testing Word COM extractor...")
try:
    from preparation.extract_para_info import extract_para_format_info
    manager1 = ParagraphManager()
    extract_para_format_info(str(doc_path), manager1)
    data1 = manager1.to_dict()
    print(f"Word COM: {len(data1)} paragraphs")
    for i, p in enumerate(data1):
        print(f"  {i}: {p.get('type')} - {p.get('content', '')[:40]}")
    with open(test_dir / 'debug_word_com.json', 'w', encoding='utf-8') as f:
        json.dump(data1, f, ensure_ascii=False, indent=2)
except Exception as e:
    print(f"Word COM error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80 + "\n")

print("Testing python-docx extractor...")
try:
    from preparation.extract_para_info_enhanced import extract_para_format_info
    manager2 = ParagraphManager()
    extract_para_format_info(str(doc_path), manager2)
    data2 = manager2.to_dict()
    print(f"python-docx: {len(data2)} paragraphs")
    for i, p in enumerate(data2):
        print(f"  {i}: {p.get('type')} - {p.get('content', '')[:40]}")
    with open(test_dir / 'debug_python_docx.json', 'w', encoding='utf-8') as f:
        json.dump(data2, f, ensure_ascii=False, indent=2)
except Exception as e:
    print(f"python-docx error: {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")
