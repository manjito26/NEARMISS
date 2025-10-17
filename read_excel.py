#!/usr/bin/env python3
"""
Script to read dropdown data from Excel file
"""
import pandas as pd
import os

def read_excel_data():
    """Read Excel data and display structure"""
    excel_file = '/home/eraser/Downloads/near_miss_data.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"Excel file not found: {excel_file}")
        return
    
    try:
        # Get all sheet names
        xl_file = pd.ExcelFile(excel_file)
        print(f"Available sheets: {xl_file.sheet_names}")
        
        # Read each sheet
        data = {}
        for sheet_name in xl_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            data[sheet_name] = df
            print(f"\nSheet: {sheet_name}")
            print(f"Columns: {df.columns.tolist()}")
            print(f"Rows: {len(df)}")
            print("First 5 rows:")
            print(df.head())
            print("-" * 50)
        
        return data
    
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

if __name__ == "__main__":
    data = read_excel_data()