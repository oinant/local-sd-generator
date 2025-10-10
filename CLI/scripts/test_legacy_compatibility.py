#!/usr/bin/env python3
"""
Test de compatibilité templates legacy (version 2.0 ancien format) avec V2 Pipeline.

Ce script teste si les templates existants (format legacy) fonctionnent
avec le nouveau système V2.0 refactorisé.

Usage:
    python3 scripts/test_legacy_compatibility.py
"""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from templating.v2.orchestrator import V2Pipeline


# Configuration
PROMPTS_DIR = Path("/mnt/d/StableDiffusion/private-new/prompts")
PATTERNS = [
    "Hassaku/Hassaku_*.prompt.yaml",
    "CyberRealistic/CyberRealisticPony_*.prompt.yaml"
]
MAIN_TEMPLATE = "Hassaku/Hassaku_Luxury_Manga_all_outfits.prompt.yaml"


def test_template(template_path: Path, pipeline: V2Pipeline) -> dict:
    """
    Test a single template and return result.

    Args:
        template_path: Path to template file
        pipeline: V2Pipeline instance

    Returns:
        Result dict with status, count, variations, or error
    """
    try:
        prompts = pipeline.run(str(template_path))

        return {
            'status': 'success',
            'file': template_path.name,
            'count': len(prompts),
            'first_variations': prompts[0].get('variations', {}) if prompts else {},
            'has_negative': bool(prompts[0].get('negative_prompt', '')) if prompts else False,
            'parameters': list(prompts[0].get('parameters', {}).keys()) if prompts else []
        }

    except FileNotFoundError as e:
        return {
            'status': 'warning',
            'file': template_path.name,
            'issue': f'Missing file: {str(e)}'
        }

    except Exception as e:
        return {
            'status': 'error',
            'file': template_path.name,
            'error_type': type(e).__name__,
            'error': str(e)
        }


def main():
    """Main test execution."""
    print("=" * 80)
    print("Legacy Template Compatibility Test")
    print("=" * 80)
    print()

    # Check if prompts directory exists
    if not PROMPTS_DIR.exists():
        print(f"❌ Prompts directory not found: {PROMPTS_DIR}")
        return 1

    print(f"📁 Prompts directory: {PROMPTS_DIR}")
    print(f"🎯 Main template: {MAIN_TEMPLATE}")
    print()

    # Initialize pipeline
    pipeline = V2Pipeline(configs_dir=str(PROMPTS_DIR))

    # Results storage
    results = {
        'success': [],
        'warnings': [],
        'errors': []
    }

    # Test each template
    print("Testing templates...")
    print("-" * 80)

    total_templates = 0
    for pattern in PATTERNS:
        for template_path in sorted(PROMPTS_DIR.glob(pattern)):
            total_templates += 1
            result = test_template(template_path, pipeline)

            # Categorize result
            status = result['status']
            if status == 'success':
                results['success'].append(result)
                print(f"✅ {result['file']}: {result['count']} prompts")
            elif status == 'warning':
                results['warnings'].append(result)
                print(f"⚠️  {result['file']}: {result['issue']}")
            else:  # error
                results['errors'].append(result)
                print(f"❌ {result['file']}: {result['error_type']}: {result['error']}")

    print()
    print("-" * 80)

    # Test main template separately (detailed output)
    main_template_path = PROMPTS_DIR / MAIN_TEMPLATE
    main_success = False

    if main_template_path.exists():
        print(f"\nTesting main template: {MAIN_TEMPLATE}")
        print("-" * 80)

        try:
            main_prompts = pipeline.run(str(main_template_path))

            print(f"✅ Main template generated {len(main_prompts)} prompts")

            if main_prompts:
                # Show first prompt details
                first = main_prompts[0]
                print(f"\n📋 First prompt details:")
                print(f"   Variations: {list(first.get('variations', {}).keys())}")
                print(f"   Parameters: {list(first.get('parameters', {}).keys())}")
                print(f"   Has negative: {bool(first.get('negative_prompt', ''))}")
                print(f"   Prompt length: {len(first.get('prompt', ''))} chars")

                # Save first 5 prompts to JSON
                output_file = Path('legacy_main_output.json')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(main_prompts[:5], f, indent=2, ensure_ascii=False)

                print(f"\n📄 First 5 prompts saved to: {output_file}")
                main_success = True
            else:
                print("⚠️  Main template generated 0 prompts")

        except Exception as e:
            print(f"❌ Main template failed: {type(e).__name__}: {e}")
    else:
        print(f"❌ Main template not found: {main_template_path}")

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total templates tested: {total_templates}")
    print(f"✅ Success: {len(results['success'])}")
    print(f"⚠️  Warnings: {len(results['warnings'])}")
    print(f"❌ Errors: {len(results['errors'])}")
    print(f"\nMain template: {'✅ OK' if main_success else '❌ FAILED'}")
    print("=" * 80)

    # Detailed errors
    if results['errors']:
        print("\n❌ ERROR DETAILS:")
        print("-" * 80)
        for err in results['errors']:
            print(f"  {err['file']}:")
            print(f"    Type: {err['error_type']}")
            print(f"    Message: {err['error']}")
        print()

    # Detailed warnings
    if results['warnings']:
        print("\n⚠️  WARNING DETAILS:")
        print("-" * 80)
        for warn in results['warnings']:
            print(f"  {warn['file']}:")
            print(f"    Issue: {warn['issue']}")
        print()

    # Save full report
    report_file = Path('legacy_compat_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"📄 Full report saved to: {report_file}")

    # Calculate success rate
    if total_templates > 0:
        success_rate = (len(results['success']) / total_templates) * 100
        print(f"\n📊 Success rate: {success_rate:.1f}% ({len(results['success'])}/{total_templates})")

    print()

    # Return exit code
    if main_success and len(results['errors']) == 0:
        return 0  # All good
    elif main_success:
        return 1  # Main OK but some errors
    else:
        return 2  # Main template failed


if __name__ == '__main__':
    sys.exit(main())
