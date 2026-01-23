
import sys
import os
import json
from pathlib import Path

# Add backend directory and project root to sys.path
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from preparation.para_type import ParagraphManager
from checkers.format_checker import FormatChecker
from utils.config_utils import load_config
from preparation.extract_para_info import extract_para_format_info

def normalize_for_comparison(value):
    """Normalize value for comparison"""
    if isinstance(value, set):
        value = list(value)
    if isinstance(value, list):
        try:
            return sorted(value)
        except TypeError:
            return value
    if isinstance(value, dict):
        return {k: normalize_for_comparison(v) for k, v in value.items()}
    if isinstance(value, float):
        return round(value, 2)
    return value

def compare_paragraph_format(actual, expected, para_id):
    """Compare paragraph format"""
    errors = []
    if 'paragraph_format' not in actual:
        errors.append(f"  Missing paragraph_format field")
        return errors

    actual_pf = actual['paragraph_format']
    expected_pf = expected['paragraph_format']

    for key in ['alignment', 'first_line_indent', 'left_indent', 'right_indent',
                'before_spacing', 'after_spacing', 'line_spacing']:
        if key in expected_pf:
            actual_val = actual_pf.get(key)
            expected_val = expected_pf[key]

            # Special handling for line_spacing
            if key == 'line_spacing':
                if isinstance(actual_val, str):
                    import re
                    match = re.search(r'(\d+\.?\d*)', actual_val)
                    if match:
                        actual_val = float(match.group(1))
                if isinstance(expected_val, str):
                    import re
                    match = re.search(r'(\d+\.?\d*)', expected_val)
                    if match:
                        expected_val = float(match.group(1))

            if actual_val != expected_val:
                errors.append(f"  {key} mismatch: expected {expected_val}, actual {actual_val}")

    return errors

def compare_fonts(actual_fonts, expected_fonts, para_id):
    """Compare font info"""
    errors = []
    
    # Check size
    if 'size' in expected_fonts:
        actual_size = normalize_for_comparison(actual_fonts.get('size', []))
        expected_size = normalize_for_comparison(expected_fonts['size'])
        if actual_size != expected_size:
            errors.append(f"  Size mismatch: expected {expected_size}, actual {actual_size}")

    # Check bold
    if 'bold' in expected_fonts:
        actual_bold = normalize_for_comparison(actual_fonts.get('bold', []))
        expected_bold = normalize_for_comparison(expected_fonts['bold'])
        if actual_bold != expected_bold:
            errors.append(f"  Bold mismatch: expected {expected_bold}, actual {actual_bold}")

    return errors

def compare_paragraphs(actual_data, expected_data):
    """Compare actual and expected paragraphs"""
    errors = []
    
    if len(actual_data) != len(expected_data):
        errors.append(f"Paragraph count mismatch: expected {len(expected_data)}, actual {len(actual_data)}")
        # If counts don't match, we still try to compare the first N
    
    min_len = min(len(actual_data), len(expected_data))
    
    for i in range(min_len):
        actual = actual_data[i]
        expected = expected_data[i]
        para_id = actual.get('id', f'para{i}')
        expected_id = expected.get('id', f'para{i}')

        # Compare type
        actual_type = actual.get('type')
        expected_type = expected.get('type')
        # Note: actual_type might be an Enum or string, expected is string
        if hasattr(actual_type, 'value'):
            actual_type = actual_type.value
            
        if actual_type != expected_type:
            errors.append(f"{para_id}: Type mismatch, expected {expected_type}, actual {actual_type}")

        # Compare content (simplified)
        actual_content = actual.get('content', '').strip()
        expected_content = expected.get('content', '').strip()
        if actual_content != expected_content:
             errors.append(f"{para_id}: Content mismatch")
             errors.append(f"  Expected: {expected_content[:50]}...")
             errors.append(f"  Actual: {actual_content[:50]}...")

        # Compare meta
        actual_meta = actual.get('meta', {})
        expected_meta = expected.get('meta', {})

        pf_errors = compare_paragraph_format(actual_meta, expected_meta, para_id)
        errors.extend(pf_errors)

        if 'fonts' in expected_meta:
            actual_fonts = actual_meta.get('fonts', {})
            expected_fonts = expected_meta['fonts']
            font_errors = compare_fonts(actual_fonts, expected_fonts, para_id)
            errors.extend(font_errors)

    return errors

def main():
    test_dir = Path(__file__).parent
    doc_path = test_dir / "测试引擎.docx"
    ground_truth_path = test_dir / "ground_truth.json"
    
    # Use default config from backend/utils/config.json
    config_path = backend_dir / "utils" / "config.json"

    if not doc_path.exists():
        print(f"Error: Test document not found: {doc_path}")
        return
    if not ground_truth_path.exists():
        print(f"Error: Ground truth not found: {ground_truth_path}")
        return
    if not config_path.exists():
        print(f"Error: Config not found: {config_path}")
        return

    # Load ground truth
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)
    
    expected_paragraphs = ground_truth.get('paragraphs', [])

    print("=" * 60)
    print("Testing Check and Preparation Logic")
    print(f"Document: {doc_path}")
    print(f"Config: {config_path}")
    print("=" * 60)

    # Run FormatChecker
    print("Running FormatChecker.analyze_format_issues...")
    checker = FormatChecker()
    # format_agent is None
    errors, actual_manager = checker.analyze_format_issues(str(doc_path), str(config_path), format_agent=None)

    # 1. Test Preparation (ParagraphManager)
    print("\n[Preparation Test Results]")
    actual_paragraphs = actual_manager.to_dict()
    
    prep_errors = compare_paragraphs(actual_paragraphs, expected_paragraphs)
    
    if not prep_errors:
        print("PASS: Paragraph extraction matches ground truth.")
    else:
        print(f"FAIL: Found {len(prep_errors)} mismatches in preparation:")
        for err in prep_errors[:20]: # Show first 20 errors
            print(f"  - {err}")
        if len(prep_errors) > 20:
            print(f"  ... and {len(prep_errors) - 20} more.")

    # 2. Test Check (Format Errors)
    print("\n[Check Test Results]")
    print(f"Found {len(errors)} format errors.")
    for err in errors:
        loc = err.get('location', 'Unknown')
        msg = err.get('message', 'No message')
        print(f"  - [{loc}] {msg}")

if __name__ == "__main__":
    main()
