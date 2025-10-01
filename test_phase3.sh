#!/bin/bash
# Test script for Phase 3 implementation

echo "=========================================="
echo "Phase 3 - JSON Config Execution Tests"
echo "=========================================="
echo ""

echo "1. Testing config selector..."
python3 -m pytest tests/test_config_selector.py -v --tb=short -q
echo ""

echo "2. Testing JSON generator..."
python3 -m pytest tests/test_json_generator.py -v --tb=short -q
echo ""

echo "3. Testing integration..."
python3 -m pytest tests/test_integration_phase3.py -v --tb=short -q
echo ""

echo "4. Testing CLI help..."
python3 CLI/generator_cli.py --help | head -5
echo ""

echo "5. Testing CLI list..."
python3 CLI/generator_cli.py --list | head -10
echo ""

echo "=========================================="
echo "All Phase 3 tests complete!"
echo "=========================================="
