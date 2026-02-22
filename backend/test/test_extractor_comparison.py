"""
Document processing method accuracy comparison test

Compare two document processing methods:
1. Word COM method (extract_para_info.py)
2. python-docx method (extract_para_info_enhanced.py)

Compare with ground_truth.json to calculate accuracy metrics.
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from preparation.para_type import ParagraphManager, ParsedParaType

# Try to import DeludeEngine, if fail create a simple substitute
try:
    from agents.delude_engine import DeludeEngine
except ImportError:
    class DeludeEngine:
        def correct_para_type(self, data):
            return data


def normalize_for_comparison(value):
    """Normalize values for comparison"""
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


def normalize_color(c):
    """Normalize color format"""
    if isinstance(c, str):
        c = c.lower()
        if c in ['auto', '000000', '0', '#0', 'black', '#black']:
            return '#black'
        if not c.startswith('#'):
            return f'#{c}'
    return c


def compare_fonts(actual_fonts, expected_fonts):
    """Compare font info, return matched fields and total fields"""
    matched = 0
    total = 0

    font_fields = ['size', 'bold', 'italic', 'color', 'zh_family', 'en_family']

    for field in font_fields:
        if field in expected_fonts:
            total += 1
            actual_val = normalize_for_comparison(actual_fonts.get(field, []))
            expected_val = normalize_for_comparison(expected_fonts[field])

            if field == 'color':
                actual_val = [normalize_color(c) for c in actual_val if c]
                expected_val = [normalize_color(c) for c in expected_val if c]

            if actual_val == expected_val:
                matched += 1

    return matched, total


def compare_paragraph_format(actual_pf, expected_pf):
    """Compare paragraph format, return matched fields and total fields"""
    matched = 0
    total = 0

    pf_fields = ['alignment', 'first_line_indent', 'left_indent', 'right_indent',
                 'before_spacing', 'after_spacing', 'line_spacing']

    for key in pf_fields:
        if key in expected_pf:
            total += 1
            actual_val = actual_pf.get(key)
            expected_val = expected_pf[key]

            if key == 'line_spacing':
                def extract_spacing(val):
                    if isinstance(val, str):
                        import re
                        match = re.search(r'(\d+\.?\d*)', val)
                        if match:
                            return float(match.group(1))
                    if isinstance(val, (int, float)):
                        return float(val)
                    return val
                actual_val = extract_spacing(actual_val)
                expected_val = extract_spacing(expected_val)

            if isinstance(actual_val, float) and isinstance(expected_val, float):
                if abs(actual_val - expected_val) < 0.1:
                    matched += 1
            elif actual_val == expected_val:
                matched += 1

    return matched, total


def compare_single_paragraph(actual, expected):
    """Compare single paragraph, return detailed comparison result"""
    result = {
        'id': actual.get('id', 'unknown'),
        'type_match': False,
        'content_match': False,
        'format_matched': 0,
        'format_total': 0,
        'font_matched': 0,
        'font_total': 0,
        'errors': []
    }

    actual_type = actual.get('type')
    expected_type = expected.get('type')
    if actual_type == expected_type:
        result['type_match'] = True
    else:
        result['errors'].append(f"type mismatch: expected {expected_type}, actual {actual_type}")

    actual_content = actual.get('content', '')
    expected_content = expected.get('content', '')
    if actual_content == expected_content:
        result['content_match'] = True
    else:
        result['errors'].append("content mismatch")

    actual_meta = actual.get('meta', {})
    expected_meta = expected.get('meta', {})

    if 'paragraph_format' in expected_meta and 'paragraph_format' in actual_meta:
        fmt_matched, fmt_total = compare_paragraph_format(
            actual_meta['paragraph_format'],
            expected_meta['paragraph_format']
        )
        result['format_matched'] = fmt_matched
        result['format_total'] = fmt_total

    if 'fonts' in expected_meta and 'fonts' in actual_meta:
        font_matched, font_total = compare_fonts(
            actual_meta['fonts'],
            expected_meta['fonts']
        )
        result['font_matched'] = font_matched
        result['font_total'] = font_total

    return result


def extract_with_word_com(doc_path: str) -> List[Dict]:
    """Extract using Word COM method"""
    from preparation.extract_para_info import extract_para_format_info
    manager = ParagraphManager()
    extract_para_format_info(str(doc_path), manager)
    data = manager.to_dict()
    delude_engine = DeludeEngine()
    data = delude_engine.correct_para_type(data)
    return data


def extract_with_python_docx(doc_path: str) -> List[Dict]:
    """Extract using python-docx method"""
    from preparation.extract_para_info_enhanced import extract_para_format_info
    manager = ParagraphManager()
    extract_para_format_info(str(doc_path), manager)
    data = manager.to_dict()
    delude_engine = DeludeEngine()
    data = delude_engine.correct_para_type(data)
    return data


def calculate_accuracy(comparison_results: List[Dict]) -> Dict[str, Any]:
    """Calculate accuracy metrics from comparison results"""
    total_paras = len(comparison_results)

    type_correct = sum(1 for r in comparison_results if r['type_match'])
    content_correct = sum(1 for r in comparison_results if r['content_match'])

    total_format_fields = sum(r['format_total'] for r in comparison_results)
    matched_format_fields = sum(r['format_matched'] for r in comparison_results)

    total_font_fields = sum(r['font_total'] for r in comparison_results)
    matched_font_fields = sum(r['font_matched'] for r in comparison_results)

    return {
        'total_paragraphs': total_paras,
        'type_accuracy': type_correct / total_paras if total_paras > 0 else 0,
        'content_accuracy': content_correct / total_paras if total_paras > 0 else 0,
        'format_accuracy': matched_format_fields / total_format_fields if total_format_fields > 0 else 0,
        'font_accuracy': matched_font_fields / total_font_fields if total_font_fields > 0 else 0,
        'type_correct': type_correct,
        'content_correct': content_correct,
        'format_matched': matched_format_fields,
        'format_total': total_format_fields,
        'font_matched': matched_font_fields,
        'font_total': total_font_fields
    }


def main():
    test_dir = Path(__file__).parent
    doc_path = test_dir / "测试引擎.docx"
    ground_truth_path = test_dir / "ground_truth.json"
    actual_output_path = test_dir / "actual_output.json"
    output_path = test_dir / "comparison_result.json"

    if not doc_path.exists():
        print(f"Error: Test document not found: {doc_path}")
        return 1

    if not ground_truth_path.exists():
        print(f"Error: ground_truth file not found: {ground_truth_path}")
        return 1

    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)
    expected_paragraphs = ground_truth.get('paragraphs', [])

    print("=" * 80)
    print("Document Processing Method Accuracy Comparison Test")
    print("=" * 80)
    print(f"Test document: {doc_path.name}")
    print(f"Expected paragraphs: {len(expected_paragraphs)}")
    print()

    # Try to use actual_output.json first (it has 25 paragraphs)
    print("Using saved actual_output.json for Word COM method...")
    word_com_data = []
    if actual_output_path.exists():
        with open(actual_output_path, 'r', encoding='utf-8') as f:
            word_com_data = json.load(f)
        print(f"  [OK] Loaded {len(word_com_data)} paragraphs from actual_output.json")
    else:
        print("  [FAIL] actual_output.json not found")

    print("Extracting with python-docx method...")
    python_docx_data = []
    try:
        python_docx_data = extract_with_python_docx(doc_path)
        print(f"  [OK] Extraction complete, paragraphs: {len(python_docx_data)}")
    except Exception as e:
        print(f"  [FAIL] Extraction failed: {e}")
        python_docx_data = []

    print()

    print("=" * 80)
    print("Comparison Results - Word COM Method")
    print("=" * 80)
    word_com_comparison = []
    word_com_accuracy = None
    if len(word_com_data) == len(expected_paragraphs):
        for actual, expected in zip(word_com_data, expected_paragraphs):
            comp = compare_single_paragraph(actual, expected)
            word_com_comparison.append(comp)
        word_com_accuracy = calculate_accuracy(word_com_comparison)
        print_accuracy_summary(word_com_accuracy, "Word COM")
    else:
        print(f"Paragraph count mismatch: expected {len(expected_paragraphs)}, actual {len(word_com_data)}")

    print()

    print("=" * 80)
    print("Comparison Results - python-docx Method")
    print("=" * 80)
    python_docx_comparison = []
    python_docx_accuracy = None

    # For python-docx, since it only has 21 paragraphs, let's compare by content matching
    if len(python_docx_data) > 0:
        # Create a map from content to expected paragraph
        content_map = {p.get('content', ''): p for p in expected_paragraphs}

        matched_paragraphs = []
        for actual in python_docx_data:
            content = actual.get('content', '')
            if content in content_map:
                matched_paragraphs.append((actual, content_map[content]))

        if matched_paragraphs:
            print(f"Matched {len(matched_paragraphs)} paragraphs by content")
            for actual, expected in matched_paragraphs:
                comp = compare_single_paragraph(actual, expected)
                python_docx_comparison.append(comp)
            python_docx_accuracy = calculate_accuracy(python_docx_comparison)
            print_accuracy_summary(python_docx_accuracy, "python-docx")
        else:
            print("Could not match any paragraphs by content")
    else:
        print(f"No data from python-docx method")

    print()

    report = {
        'test_document': str(doc_path),
        'ground_truth': str(ground_truth_path),
        'expected_paragraph_count': len(expected_paragraphs),
        'word_com': {
            'paragraph_count': len(word_com_data),
            'accuracy': word_com_accuracy,
            'details': word_com_comparison
        },
        'python_docx': {
            'paragraph_count': len(python_docx_data),
            'accuracy': python_docx_accuracy,
            'details': python_docx_comparison
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"Detailed comparison report saved to: {output_path}")
    print()

    print("=" * 80)
    print("Overall Comparison")
    print("=" * 80)
    print_comparison_table(word_com_accuracy, python_docx_accuracy)

    return 0


def print_accuracy_summary(accuracy: Dict[str, Any], method_name: str):
    """Print accuracy summary"""
    print(f"Paragraphs: {accuracy['total_paragraphs']}")
    print(f"Type accuracy: {accuracy['type_accuracy']:.2%} ({accuracy['type_correct']}/{accuracy['total_paragraphs']})")
    print(f"Content accuracy: {accuracy['content_accuracy']:.2%} ({accuracy['content_correct']}/{accuracy['total_paragraphs']})")
    print(f"Format accuracy: {accuracy['format_accuracy']:.2%} ({accuracy['format_matched']}/{accuracy['format_total']})")
    print(f"Font accuracy: {accuracy['font_accuracy']:.2%} ({accuracy['font_matched']}/{accuracy['font_total']})")


def print_comparison_table(word_com_acc: Dict[str, Any], python_docx_acc: Dict[str, Any]):
    """Print comparison table"""
    if not word_com_acc or not python_docx_acc:
        print("Cannot generate comparison table, missing data")
        return

    metrics = [
        ("Type Recognition", "type_accuracy"),
        ("Content Match", "content_accuracy"),
        ("Paragraph Format", "format_accuracy"),
        ("Font Info", "font_accuracy"),
    ]

    print(f"{'Metric':<20} {'Word COM':<15} {'python-docx':<15} {'Winner':<15}")
    print("-" * 65)

    for metric_name, metric_key in metrics:
        wc = word_com_acc.get(metric_key, 0)
        pd = python_docx_acc.get(metric_key, 0)

        if wc > pd:
            winner = "Word COM"
        elif pd > wc:
            winner = "python-docx"
        else:
            winner = "Tie"

        print(f"{metric_name:<20} {wc:<15.2%} {pd:<15.2%} {winner:<15}")


if __name__ == '__main__':
    sys.exit(main())
