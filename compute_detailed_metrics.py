#!/usr/bin/env python3
"""
Hi folks, 
In this file/script I computed detailed dashboard metrics from the BlinkIT Excel dataset.

All metrics shown in the dashboard including:
- KPI cards (total/avg sales, items, rating)
- Time series by establishment year
- Fat content breakdowns
- Item type sales
- Fat by outlet tier
- Outlet size/location/type statistics
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np


def find_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first matching column name from candidates (case-insensitive, substring match)."""
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        cand_l = cand.lower()
        # exact match
        for k, orig in cols.items():
            if k == cand_l:
                return orig
        # substring match
        for k, orig in cols.items():
            if cand_l in k:
                return orig
    return None


def format_currency(val: float, precision: int = 2) -> str:
    """Format a value as currency with K/M suffix."""
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:.{precision}f}M"
    if abs(val) >= 1_000:
        return f"${val/1_000:.{precision}f}K"
    return f"${val:.{precision}f}"


def compute_metrics(df: pd.DataFrame) -> Dict:
    # detect columns
    sales_col = find_column(df, ['Sales', 'Item Outlet Sales', 'Item_Sales', 'Total Sales'])
    rating_col = find_column(df, ['Rating', 'Item_Outlet_Rating', 'Avg Rating'])
    item_id_col = find_column(df, ['Item Identifier', 'Item ID', 'Item_Identifier', 'ItemID', 'Item_Id'])
    item_type_col = find_column(df, ['Item Type', 'Item_Type', 'ItemType'])
    fat_col = find_column(df, ['Item Fat Content', 'Fat Content', 'Fat'])
    outlet_size_col = find_column(df, ['Outlet Size', 'Outlet_Size', 'Size'])
    outlet_loc_col = find_column(df, ['Outlet Location Type', 'Outlet Location', 'Outlet_Location_Type', 'Location Type'])
    outlet_type_col = find_column(df, ['Outlet Type', 'Outlet_Type', 'OutletType'])
    item_visibility_col = find_column(df, ['Item Visibility', 'Visibility'])
    outlet_year_col = find_column(df, ['Outlet Establishment Year', 'Year', 'Establishment Year'])

    metrics: Dict = {}

    if sales_col is None:
        raise KeyError('Could not find a Sales column in the sheet (candidates: Sales)')

    # ensure numeric columns
    df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce').fillna(0.0)
    if rating_col:
        df[rating_col] = pd.to_numeric(df[rating_col], errors='coerce')
    if item_visibility_col:
        df[item_visibility_col] = pd.to_numeric(df[item_visibility_col], errors='coerce')
    if outlet_year_col:
        df[outlet_year_col] = pd.to_numeric(df[outlet_year_col], errors='coerce')

    # TOP METRICS (KPI Cards)
    total_sales = float(df[sales_col].sum())
    metrics['kpi'] = {
        'total_sales': format_currency(total_sales),
        'total_sales_raw': total_sales,
        'average_sales': format_currency(float(df[sales_col].mean())),
        'no_of_items': int(len(df)),  # dashboard uses total rows not unique
        'avg_rating': float(df[rating_col].mean()) if rating_col else None
    }

    # OUTLET ESTABLISHMENT (Time Series)
    if outlet_year_col:
        yearly = df.groupby(outlet_year_col)[sales_col].sum().sort_index()
        metrics['sales_by_year'] = {
            int(year): format_currency(sales)
            for year, sales in yearly.items()
        }
        peak_year = yearly.idxmax()
        metrics['peak_sales_year'] = {
            'year': int(peak_year),
            'sales': format_currency(yearly[peak_year])
        }

    # FAT CONTENT
    if fat_col and fat_col in df.columns:
        fat = df.groupby(fat_col)[sales_col].sum().sort_values(ascending=False)
        metrics['fat_content'] = {
            k: format_currency(v) for k, v in fat.items()
        }
        metrics['fat_content_raw'] = fat.to_dict()

    # ITEM TYPE (Sales by Category)
    if item_type_col and item_type_col in df.columns:
        item_type = df.groupby(item_type_col)[sales_col].sum().sort_values(ascending=False)
        metrics['sales_by_item_type'] = {
            k: format_currency(v) for k, v in item_type.items()
        }
        metrics['sales_by_item_type_raw'] = item_type.to_dict()
        # Find top categories
        top_cats = item_type.nlargest(2)
        metrics['top_categories'] = [
            {'name': k, 'sales': format_currency(v)}
            for k, v in top_cats.items()
        ]

    # FAT BY OUTLET (Tier Distribution)
    if fat_col and outlet_loc_col:
        fat_tier = df.groupby([outlet_loc_col, fat_col])[sales_col].sum().unstack()
        metrics['fat_by_tier'] = {
            tier: {
                col: format_currency(val)
                for col, val in row.items()
            }
            for tier, row in fat_tier.iterrows()
        }
        metrics['fat_by_tier_raw'] = fat_tier.to_dict()

    # OUTLET SIZE
    if outlet_size_col:
        size = df.groupby(outlet_size_col)[sales_col].sum()
        metrics['sales_by_outlet_size'] = {
            k: format_currency(v) for k, v in size.items()
        }
        metrics['sales_by_outlet_size_raw'] = size.to_dict()

    # OUTLET LOCATION (by Tier)
    if outlet_loc_col:
        loc = df.groupby(outlet_loc_col)[sales_col].sum().sort_values(ascending=False)
        max_loc = loc.max()
        metrics['sales_by_location'] = {
            tier: {
                'sales': format_currency(sales),
                'pct': f"{(sales/max_loc*100):.1f}%"
            }
            for tier, sales in loc.items()
        }
        metrics['sales_by_location_raw'] = loc.to_dict()

    # OUTLET TYPE (Detailed Breakdown)
    if outlet_type_col and outlet_type_col in df.columns:
        g = df.groupby(outlet_type_col).agg({
            sales_col: ['sum', 'mean'],
            item_id_col if item_id_col else sales_col: 'count',
            rating_col: 'mean' if rating_col else 'count',
            item_visibility_col: 'sum' if item_visibility_col else 'count'
        }).fillna(0)
        
        # Rename columns
        g.columns = ['total_sales', 'average_sales', 'no_of_items', 'avg_rating', 'item_visibility']
        
        # Format for display
        metrics['outlet_type_breakdown'] = {
            outlet: {
                'total_sales': format_currency(row['total_sales']),
                'no_of_items': int(row['no_of_items']),
                'average_sales': format_currency(row['average_sales']),
                'avg_rating': round(float(row['avg_rating'])) if pd.notna(row['avg_rating']) else None,
                'item_visibility': float(row['item_visibility']) if pd.notna(row['item_visibility']) else None
            }
            for outlet, row in g.iterrows()
        }
        metrics['outlet_type_breakdown_raw'] = g.to_dict()
        
        # Find best performing outlet
        best = g['total_sales'].idxmax()
        metrics['best_performing_outlet'] = {
            'name': best,
            'sales': format_currency(g.loc[best, 'total_sales'])
        }

    return metrics


def main():
    parser = argparse.ArgumentParser(description='Compute detailed dashboard metrics from BlinkIT Excel file')
    parser.add_argument('excel', help='Path to the Excel file')
    parser.add_argument('--out-dir', help='Directory to write outputs', default='.')
    parser.add_argument('--sheet', help='Sheet name (defaults to first sheet)', default=None)
    args = parser.parse_args()

    excel_path = Path(args.excel)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # load sheet
    if args.sheet:
        df = pd.read_excel(excel_path, sheet_name=args.sheet)
    else:
        df = pd.read_excel(excel_path)

    metrics = compute_metrics(df)

    # Save JSON with all metrics
    out_json = out_dir / 'detailed_metrics.json'
    with open(out_json, 'w', encoding='utf8') as f:
        json.dump(metrics, f, indent=2)

    # Print formatted summary comparing to dashboard values
    print('\nDashboard Metrics Comparison:')
    print('\nTOP METRICS (KPI Cards)')
    print(f"Total Sales: {metrics['kpi']['total_sales']} (Dashboard: $1.20M)")
    print(f"Average Sales: {metrics['kpi']['average_sales']} (Dashboard: $141)")
    print(f"No. of Items: {metrics['kpi']['no_of_items']:,} (Dashboard: 8,523)")
    if metrics['kpi']['avg_rating']:
        print(f"Average Rating: {metrics['kpi']['avg_rating']:.1f} (Dashboard: 3.9)")

    if 'sales_by_year' in metrics:
        print('\nOUTLET ESTABLISHMENT (Time Series)')
        for year in sorted(metrics['sales_by_year'].keys()):
            print(f"{year}: {metrics['sales_by_year'][year]}")
        if 'peak_sales_year' in metrics:
            print(f"Peak year: {metrics['peak_sales_year']['year']} with {metrics['peak_sales_year']['sales']}")

    if 'fat_content' in metrics:
        print('\nFAT CONTENT')
        for k, v in metrics['fat_content'].items():
            print(f"{k}: {v}")

    if 'sales_by_item_type' in metrics:
        print('\nITEM TYPE (Sales by Category)')
        for k, v in metrics['sales_by_item_type'].items():
            print(f"{k}: {v}")

    if 'fat_by_tier' in metrics:
        print('\nFAT BY OUTLET (Tier Distribution)')
        for tier, data in metrics['fat_by_tier'].items():
            print(f"\n{tier}:")
            for fat, sales in data.items():
                print(f"- {fat}: {sales}")

    if 'sales_by_outlet_size' in metrics:
        print('\nOUTLET SIZE')
        for size, sales in metrics['sales_by_outlet_size'].items():
            print(f"{size}: {sales}")

    if 'sales_by_location' in metrics:
        print('\nOUTLET LOCATION (by Tier)')
        for loc, data in metrics['sales_by_location'].items():
            print(f"{loc}: {data['sales']} ({data['pct']})")

    if 'outlet_type_breakdown' in metrics:
        print('\nOUTLET TYPE (Detailed Breakdown)')
        for outlet, data in metrics['outlet_type_breakdown'].items():
            print(f"\n{outlet}:")
            for k, v in data.items():
                print(f"- {k}: {v}")

    print(f"\nSaved detailed metrics -> {out_json}")


if __name__ == '__main__':
    main()