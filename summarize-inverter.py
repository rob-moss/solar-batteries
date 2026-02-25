#!/usr/bin/env python3
"""Summarize solar inverter data by hour-of-day.

Reads 'Solar inverter data 1Feb25-23Feb26.csv' and creates
'Solar Inverter data summary 1Feb25-23Feb26.csv' with 24 rows (00-23).

Output columns:
- Hour of day (00-23)
- Energy From the Grid (kWh)
- Energy To the Grid (kWh)

All input energy columns are in Wh; output is in kWh (sum/1000).
"""
import csv
from datetime import datetime
from collections import defaultdict
import sys

INPUT = 'Solar inverter data 1Feb25-23Feb26.csv'
OUTPUT = 'Solar Inverter data summary 1Feb25-23Feb26.csv'


def parse_datetime(dt_str):
    # Try common formats observed in the CSV: '01.02.2025 00:00'
    fmts = ['%d.%m.%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M']
    for f in fmts:
        try:
            return datetime.strptime(dt_str, f)
        except Exception:
            continue
    # If parsing fails, return None
    return None


def to_float(val):
    if val is None or val == '':
        return 0.0
    try:
        return float(val)
    except Exception:
        # strip commas
        try:
            return float(val.replace(',', ''))
        except Exception:
            return 0.0


def main():
    hourly_from = defaultdict(float)  # Wh
    hourly_to = defaultdict(float)

    try:
        with open(INPUT, 'r', newline='') as f:
            reader = csv.DictReader(f)
            # Normalize fieldnames (remove BOM if present)
            if reader.fieldnames:
                reader.fieldnames = [fn.lstrip('\ufeff') if isinstance(fn, str) else fn for fn in reader.fieldnames]
            # Check expected columns
            if 'Date and time' not in reader.fieldnames:
                print('ERROR: expected "Date and time" column in CSV')
                return 1

            # Determine column names for energy
            col_from = 'Energy from grid (Wh)'
            col_to = 'Energy to grid (Wh)'
            if col_from not in reader.fieldnames or col_to not in reader.fieldnames:
                print('ERROR: expected energy columns not found')
                return 1

            for row in reader:
                dt_text = row.get('Date and time', '').strip()
                if not dt_text:
                    continue
                dt = parse_datetime(dt_text)
                if dt is None:
                    # skip rows we can't parse
                    continue
                hour = dt.hour  # 0..23

                val_from = to_float(row.get(col_from))
                val_to = to_float(row.get(col_to))

                hourly_from[hour] += val_from
                hourly_to[hour] += val_to

    except FileNotFoundError:
        print(f'ERROR: input file "{INPUT}" not found')
        return 1

    # Write output CSV with hours 00..23
    with open(OUTPUT, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Hour of day', 'Energy From the Grid (kWh)', 'Energy To the Grid (kWh)'])
        for h in range(24):
            from_kwh = hourly_from.get(h, 0.0) / 1000.0
            to_kwh = hourly_to.get(h, 0.0) / 1000.0
            writer.writerow([f'{h:02d}', f'{from_kwh:.3f}', f'{to_kwh:.3f}'])

    print(f'Wrote summary to {OUTPUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
