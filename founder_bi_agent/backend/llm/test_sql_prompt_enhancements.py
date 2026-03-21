#!/usr/bin/env python3
"""
Validation test for SQL generation improvements and prompt enhancements.
Tests the new system prompt against common failure patterns.
"""

import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from founder_bi_agent.backend.llm.sql_prompt_context import (
    SYSTEM_PROMPT_SQL_GENERATION,
    create_validation_hint,
    TABLE_METADATA_CONTEXT
)


def test_system_prompt_structure():
    """Verify system prompt contains all critical warnings"""
    print("=" * 60)
    print("TEST 1: System Prompt Contains Critical Warnings")
    print("=" * 60)
    
    critical_items = [
        ("created_at field", "created_at"),
        ("Timestamp mention", "timestamp"),
        ("Sector 'Mining'", "Mining"),
        ("Sector 'Railway' warning", "NOT Railway"),
        ("TRY_CAST guidance", "TRY_CAST"),
        ("GROUP BY requirement", "GROUP BY"),
        ("RFC3339 format", "RFC3339"),
        ("DATE_TRUNC usage", "DATE_TRUNC"),
    ]
    
    all_passed = True
    for check_name, expected_phrase in critical_items:
        if expected_phrase in SYSTEM_PROMPT_SQL_GENERATION:
            print(f"✅ {check_name}: FOUND")
        else:
            print(f"❌ {check_name}: MISSING - expected '{expected_phrase}'")
            all_passed = False
    
    return all_passed


def test_validation_hint():
    """Verify validation hint covers all key checks"""
    print("\n" + "=" * 60)
    print("TEST 2: Validation Hint Completeness")
    print("=" * 60)
    
    hint = create_validation_hint()
    checks = [
        "created_at",
        "TRY_CAST",
        "GROUP BY",
        "RFC3339",
        "timestamp",
    ]
    
    all_passed = True
    for check in checks:
        if check in hint:
            print(f"✅ Hint includes: {check}")
        else:
            print(f"❌ Hint missing: {check}")
            all_passed = False
    
    return all_passed


def test_table_metadata():
    """Verify table metadata has correct content"""
    print("\n" + "=" * 60)
    print("TEST 3: Table Metadata Context")
    print("=" * 60)
    
    all_passed = True
    
    # Check deals table
    if "deals" in TABLE_METADATA_CONTEXT:
        deals = TABLE_METADATA_CONTEXT["deals"]
        print(f"✅ Deals table found with {deals['row_count']} rows")
        
        if "sectorservice" in deals["key_columns"]:
            sector_info = deals["key_columns"]["sectorservice"]
            valid_values = sector_info.get("values", [])
            
            expected_sectors = ['Mining', 'Powerline', 'Renewables', 'Tender']
            if set(valid_values) == set(expected_sectors):
                print(f"✅ Valid sectors: {', '.join(valid_values)}")
            else:
                print(f"❌ Invalid sectors: expected {expected_sectors}, got {valid_values}")
                all_passed = False
            
            # Check for Railway warning
            if "NOT Railway" in sector_info.get("note", ""):
                print("✅ Railway non-inclusion warning present")
            else:
                print("❌ Railway warning missing")
                all_passed = False
        else:
            print("❌ sectorservice column not found in metadata")
            all_passed = False
    else:
        print("❌ Deals table not found in metadata")
        all_passed = False
    
    # Check work_orders table
    if "work_orders" in TABLE_METADATA_CONTEXT:
        print(f"✅ Work orders table found with {TABLE_METADATA_CONTEXT['work_orders']['row_count']} rows")
    else:
        print("❌ Work orders table not found")
        all_passed = False
    
    return all_passed


def test_example_sql_patterns():
    """Verify system prompt contains correct SQL examples"""
    print("\n" + "=" * 60)
    print("TEST 4: Example SQL Patterns")
    print("=" * 60)
    
    all_passed = True
    
    # Check for correct timestamp example
    if "TRY_CAST(created_at AS TIMESTAMP)" in SYSTEM_PROMPT_SQL_GENERATION:
        print("✅ Correct timestamp casting example found")
    else:
        print("❌ Correct timestamp casting example missing")
        all_passed = False
    
    # Check for DATE_TRUNC example
    if "DATE_TRUNC" in SYSTEM_PROMPT_SQL_GENERATION:
        print("✅ DATE_TRUNC for timestamp extraction found")
    else:
        print("❌ DATE_TRUNC example missing")
        all_passed = False
    
    # Check for correct sector example
    if "Mining" in SYSTEM_PROMPT_SQL_GENERATION and "Powerline" in SYSTEM_PROMPT_SQL_GENERATION:
        print("✅ Correct sector values in examples")
    else:
        print("❌ Sector examples incomplete")
        all_passed = False
    
    # Check for GROUP BY example
    if "GROUP BY" in SYSTEM_PROMPT_SQL_GENERATION:
        print("✅ GROUP BY rule documented")
    else:
        print("❌ GROUP BY rule missing")
        all_passed = False
    
    return all_passed


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "🔍 SQL Generation Prompt Validation Tests" + "\n")
    
    results = []
    results.append(("System Prompt Structure", test_system_prompt_structure()))
    results.append(("Validation Hint", test_validation_hint()))
    results.append(("Table Metadata", test_table_metadata()))
    results.append(("Example SQL Patterns", test_example_sql_patterns()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
