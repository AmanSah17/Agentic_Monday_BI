#!/usr/bin/env python
"""Analyze real data from Excel files for pipeline calibration"""

import pandas as pd
import json
from pathlib import Path

excel_dir = Path("f:/downloads_chrome")

print("=" * 80)
print("DEAL FUNNEL DATA ANALYSIS")
print("=" * 80)

try:
    deals_df = pd.read_excel(excel_dir / 'Deal funnel Data.xlsx', sheet_name='Deal tracker')
    print(f"\nShape: {deals_df.shape[0]} rows × {deals_df.shape[1]} columns")
    print(f"\nColumns: {list(deals_df.columns)}")
    print(f"\nData Types:")
    for col, _type in deals_df.dtypes.items():
        print(f"  {col}: {_type}")
    
    print(f"\nFirst 3 rows:")
    print(deals_df.head(3).to_string())
    
    print(f"\n\nCategorical/Low-Cardinality Columns:")
    for col in deals_df.columns:
        if deals_df[col].dtype == 'object' or deals_df[col].nunique() < 20:
            unique_vals = deals_df[col].dropna().unique()
            print(f"  {col}: {deals_df[col].nunique()} unique")
            print(f"    Values: {list(unique_vals[:15])}")

except Exception as e:
    print(f"ERROR reading deals: {e}")

print("\n" + "=" * 80)
print("WORK ORDER TRACKER DATA ANALYSIS")
print("=" * 80)

try:
    wo_df = pd.read_excel(excel_dir / 'Work_Order_Tracker Data.xlsx', sheet_name='work order tracker')
    print(f"\nShape: {wo_df.shape[0]} rows × {wo_df.shape[1]} columns")
    print(f"\nColumns: {list(wo_df.columns)}")
    print(f"\nData Types:")
    for col, _type in wo_df.dtypes.items():
        print(f"  {col}: {_type}")
    
    print(f"\nFirst 3 rows:")
    print(wo_df.head(3).to_string())
    
    print(f"\n\nCategorical/Low-Cardinality Columns:")
    for col in wo_df.columns:
        if wo_df[col].dtype == 'object' or wo_df[col].nunique() < 20:
            unique_vals = wo_df[col].dropna().unique()
            print(f"  {col}: {wo_df[col].nunique()} unique")
            print(f"    Values: {list(unique_vals[:15])}")

except Exception as e:
    print(f"ERROR reading work orders: {e}")

print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

try:
    deals_df = pd.read_excel(excel_dir / 'Deal funnel Data.xlsx', sheet_name='Deal tracker')
    print(f"\nDeals - Numeric columns summary:")
    print(deals_df.describe().to_string())
except:
    pass

try:
    wo_df = pd.read_excel(excel_dir / 'Work_Order_Tracker Data.xlsx', sheet_name='work order tracker')
    print(f"\n\nWork Orders - Numeric columns summary:")
    print(wo_df.describe().to_string())
except:
    pass
