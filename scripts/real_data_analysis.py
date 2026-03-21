"""
Real Data Analysis & Test Plan for FounderBI Agent
Prepared: March 21, 2026

This document aligns the BI pipeline with ACTUAL Monday.com data structure.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Read actual data
excel_dir = Path("f:/downloads_chrome")
deals_df = pd.read_excel(excel_dir / 'Deal funnel Data.xlsx', sheet_name='Deal tracker')
wo_df = pd.read_excel(excel_dir / 'Work_Order_Tracker Data.xlsx', sheet_name='work order tracker', header=1)

print("=" * 100)
print("REAL DATA STRUCTURE ANALYSIS FOR MONDAY.COM BI AGENT")
print("=" * 100)

# ============================================================================
# DEALS DATA ANALYSIS
# ============================================================================
print("\n📊 DEALS TABLE (Deal funnel Data)")
print("-" * 100)
print(f"Rows: {len(deals_df)} | Columns: {len(deals_df.columns)}")
print(f"\nColumn Structure:")
for col in deals_df.columns:
    dtype = deals_df[col].dtype
    non_null = deals_df[col].notna().sum()
    unique = deals_df[col].nunique()
    sample = deals_df[col].dropna().iloc[0] if non_null > 0 else "N/A"
    print(f"  • {col:<35} | dtype: {str(dtype):<10} | non-null: {non_null:>3} | unique: {unique:>4} | sample: {str(sample)[:50]}")

print(f"\n✅ CATEGORICAL ANALYSIS (Deals):")
for col in ['Deal Status', 'Deal Stage', 'Product deal', 'Sector/service']:
    if col in deals_df.columns:
        values = deals_df[col].dropna().unique()
        print(f"  {col}: {list(values)}")

print(f"\n💰 FINANCIAL METRICS (Deals):")
if 'Masked Deal value' in deals_df.columns:
    val_col = deals_df['Masked Deal value']
    print(f"  Total Value: {val_col.sum():,.0f}")
    print(f"  Mean: {val_col.mean():,.0f}")
    print(f"  Min: {val_col.min():,.0f}")
    print(f"  Max: {val_col.max():,.0f}")
    print(f"  Median: {val_col.median():,.0f}")

print(f"\n📅 DATE RANGES (Deals):")
if 'Created Date' in deals_df.columns:
    dates = pd.to_datetime(deals_df['Created Date'], errors='coerce')
    print(f"  Created Date range: {dates.min()} to {dates.max()}")
if 'Close Date (A)' in deals_df.columns:
    dates = pd.to_datetime(deals_df['Close Date (A)'], errors='coerce')
    print(f"  Close Date range: {dates.min()} to {dates.max()}")

# ============================================================================
# WORK ORDERS DATA ANALYSIS
# ============================================================================
print("\n" + "=" * 100)
print("📦 WORK ORDERS TABLE (Work_Order_Tracker)")
print("-" * 100)
print(f"Rows: {len(wo_df)} | Columns: {len(wo_df.columns)}")
print(f"\nColumn Structure (Key Columns):")
key_cols = ['Deal name masked', 'Sector', 'Execution Status', 'Nature of Work', 'WO Status (billed)', 
            'Billing Status', 'Collection status', 'Amount in Rupees (Excl of GST) (Masked)']
for col in key_cols:
    if col in wo_df.columns:
        dtype = wo_df[col].dtype
        non_null = wo_df[col].notna().sum()
        unique = wo_df[col].nunique()
        sample = wo_df[col].dropna().iloc[0] if non_null > 0 else "N/A"
        print(f"  • {col:<45} | dtype: {str(dtype):<10} | non-null: {non_null:>3} | unique: {unique:>2} | sample: {str(sample)[:40]}")

print(f"\n✅ CATEGORICAL ANALYSIS (Work Orders):")
for col in ['Execution Status', 'Sector', 'Type of Work', 'WO Status (billed)', 'Billing Status', 'Collection status']:
    if col in wo_df.columns:
        values = wo_df[col].dropna().unique()
        print(f"  {col}: {list(values)[:10]}")

print(f"\n💰 FINANCIAL METRICS (Work Orders):")
if 'Amount in Rupees (Excl of GST) (Masked)' in wo_df.columns:
    val_col = pd.to_numeric(wo_df['Amount in Rupees (Excl of GST) (Masked)'], errors='coerce')
    print(f"  Total Amount: {val_col.sum():,.0f}")
    print(f"  Mean: {val_col.mean():,.0f}")
    print(f"  Median: {val_col.median():,.0f}")

print(f"\n📅 DATE COLUMNS (Work Orders):")
date_cols = ['Date of PO/LOI', 'Probable Start Date', 'Probable End Date', 'Last invoice date', 'Expected Billing Month', 'Actual Billing Month', 'Actual Collection Month', 'Collection Date']
for col in date_cols:
    if col in wo_df.columns:
        dates = pd.to_datetime(wo_df[col], errors='coerce')
        if dates.notna().sum() > 0:
            print(f"  {col}: {dates.min()} to {dates.max()}")

# ============================================================================
# KEY INSIGHTS FOR PIPELINE
# ============================================================================
print("\n" + "=" * 100)
print("🎯 KEY INSIGHTS FOR PIPELINE CALIBRATION")
print("=" * 100)

print(f"\n1. NAMING CONVENTIONS")
print(f"   ✓ Deal table uses 'Sector/service' (not 'Sector')")
print(f"   ✓ Deal table uses 'Deal Status' + 'Deal Stage' (dual status fields)")
print(f"   ✓ Deal value column: 'Masked Deal value' (privacy-masked)")
print(f"   ✓ Work order date headers have inconsistent naming (some with special characters)")

print(f"\n2. DATA QUALITY OBSERVATIONS")
deals_with_value = deals_df['Masked Deal value'].notna().sum()
print(f"   ✓ Deals with values: {deals_with_value}/{len(deals_df)} ({100*deals_with_value/len(deals_df):.1f}%)")
wo_with_amount = wo_df['Amount in Rupees (Excl of GST) (Masked)'].notna().sum()
print(f"   ✓ Work orders with amounts: {wo_with_amount}/{len(wo_df)} ({100*wo_with_amount/len(wo_df):.1f}%)")

print(f"\n3. POTENTIAL JOIN KEYS")
print(f"   • Deals: 'Deal Name' (unique identifier)")
print(f"   • WO: 'Deal name masked' (matches Deals 'Deal Name')")
print(f"   • Recommendation: Use Deal Name as primary join key")

print(f"\n4. QUESTIONS TO TEST")
print(f"   Q1: 'What is the total deal value by sector?'")
print(f"   Q2: 'Which deals are in which stage?'")
print(f"   Q3: 'What is the status of work orders by execution?'")
print(f"   Q4: 'Deal-to-WO mapping: which deals have work orders?'")
print(f"   Q5: 'Revenue recognition: billed vs collected amounts'")
print(f"   Q6: 'Pipeline forecast: close probability vs tentative dates'")
print(f"   Q7: 'Top clients by deal value'")
print(f"   Q8: 'Work order execution status breakdown'")

print("\n" + "=" * 100)
