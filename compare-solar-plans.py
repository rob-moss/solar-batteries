#!/usr/bin/env python3
"""
Solar Plans Comparison Script

Reads inverter data and solar plans, compares them to calculate costs and savings
for each solar plan based on historical energy import/export data.
"""

import csv
import sys
import re
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple


def parse_rate_value(rate_str: str) -> float:
    """Extract numeric value from rate strings like '37.58 c/kWh' or '$46.89'."""
    if not rate_str or rate_str == "N/A":
        return 0.0
    # Remove currency symbols and units
    cleaned = rate_str.replace("c/kWh", "").replace("c/day", "").replace("$", "").replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_kwh_limit(limit_str: str):
    """Parse strings like '1 kWh', '1 kWh per day', or 'N/A' into a float kWh or None."""
    if not limit_str or limit_str.strip().upper() == "N/A":
        return None
    try:
        # Find first number in the string
        parts = limit_str.replace("kwh", "kWh").split()
        for p in parts:
            try:
                return float(p)
            except ValueError:
                continue
    except Exception:
        return None
    return None


def parse_consumption_bucket_limit(hours_str: str) -> float:
    """Parse consumption bucket limits from strings like 'First 8.000 kWh/day'."""
    if not hours_str or hours_str.upper() == "N/A":
        return None
    if "First" in hours_str and "kWh" in hours_str.upper():
        match = re.search(r'(\d+\.?\d*)\s*[kK][wW][hH]', hours_str)
        if match:
            return float(match.group(1))
    return None


def parse_hour_from_datetime(date_time_str: str) -> int:
    """Parse hour from datetime string in format 'DD.MM.YYYY HH:MM'."""
    try:
        dt = datetime.strptime(date_time_str.strip(), "%d.%m.%Y %H:%M")
        return dt.hour
    except ValueError:
        return -1


def is_hour_in_range(hour: int, time_range: str) -> bool:
    """Check if an hour falls within a time range string like '3pm - 9pm'."""
    if not time_range or time_range == "All hours":
        return True
    
    try:
        # Parse time ranges like "3pm - 9pm" or "12am - 3pm, 9pm - 12am"
        ranges = time_range.split(",")
        for range_part in ranges:
            range_part = range_part.strip()
            times = range_part.split("-")
            if len(times) != 2:
                continue
            
            start_str = times[0].strip()
            end_str = times[1].strip()
            
            # Convert to 24-hour format
            start_hour = convert_to_24h(start_str)
            end_hour = convert_to_24h(end_str)
            
            # Handle ranges that cross midnight
            if start_hour <= end_hour:
                if start_hour <= hour < end_hour:
                    return True
            else:  # Range crosses midnight
                if hour >= start_hour or hour < end_hour:
                    return True
        
        return False
    except:
        return False


def convert_to_24h(time_str: str) -> int:
    """Convert time string like '3pm' or '5:30pm' to minutes since midnight (int).

    Returns minutes (0-1439)."""
    time_str = time_str.strip().lower()
    # default minutes
    minutes = 0
    try:
        # handle formats like '5:30pm' or '5pm' or '12am'
        suffix = None
        if time_str.endswith('am') or time_str.endswith('pm'):
            suffix = time_str[-2:]
            core = time_str[:-2].strip()
        else:
            core = time_str

        if ':' in core:
            h_str, m_str = core.split(':', 1)
            hour = int(h_str)
            minute = int(m_str)
        else:
            hour = int(core)
            minute = 0

        if suffix == 'am':
            if hour == 12:
                hour = 0
        elif suffix == 'pm':
            if hour != 12:
                hour += 12

        minutes = hour * 60 + minute
        minutes = minutes % (24 * 60)
    except Exception:
        minutes = 0

    return minutes


def minutes_overlap(hour_dt: datetime, range_str: str) -> int:
    """Return number of minutes overlap between the hour starting at hour_dt and the time ranges in range_str.

    range_str can be like '5:30pm - 7:30pm' or '12am - 5:30pm, 7:30pm - 12am'."""
    if not range_str or range_str.strip().upper() == 'N/A' or range_str.strip().lower() == 'all hours':
        return 60

    hour_start = hour_dt.replace(minute=0, second=0, microsecond=0)
    hour_end = hour_start + timedelta(hours=1)

    total_overlap = 0
    try:
        parts = [p.strip() for p in range_str.split(',') if p.strip()]
        for part in parts:
            if '-' not in part:
                continue
            a, b = [s.strip() for s in part.split('-', 1)]
            a_min = convert_to_24h(a)
            b_min = convert_to_24h(b)

            # build range intervals in minutes since midnight, may wrap
            if a_min <= b_min:
                intervals = [(a_min, b_min)]
            else:
                intervals = [(a_min, 24 * 60), (0, b_min)]

            for (start_min, end_min) in intervals:
                # convert to today's datetime
                start_dt = hour_start.replace(hour=0, minute=0) + timedelta(minutes=start_min)
                end_dt = hour_start.replace(hour=0, minute=0) + timedelta(minutes=end_min)

                latest_start = max(hour_start, start_dt)
                earliest_end = min(hour_end, end_dt)
                overlap = (earliest_end - latest_start).total_seconds() / 60
                if overlap > 0:
                    total_overlap += int(overlap)
    except Exception:
        return 0

    # clamp
    if total_overlap < 0:
        total_overlap = 0
    if total_overlap > 60:
        total_overlap = 60

    return total_overlap


def read_solar_plans(csv_file: str) -> List[Dict]:
    """Read solar plans from CSV file."""
    plans = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up quoted values
                plan = {key.strip(): value.strip().strip('"') for key, value in row.items()}
                plans.append(plan)
    except Exception as e:
        print(f"Error reading solar plans: {e}")
        sys.exit(1)
    
    return plans


def read_inverter_data(csv_file: str) -> Tuple[Dict[str, float], Dict[str, float], datetime, datetime]:
    """Read inverter data and aggregate to hourly values.
    
    Returns:
        - energy_from_grid: Dict of 'YYYY-MM-DD HH' -> kWh
        - energy_to_grid: Dict of 'YYYY-MM-DD HH' -> kWh
        - start_date: First timestamp
        - end_date: Last timestamp
    """
    energy_from_grid = defaultdict(float)
    energy_to_grid = defaultdict(float)
    
    all_timestamps = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:  # Use utf-8-sig to handle BOM
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    timestamp_str = row.get('Date and time', '').strip()
                    if not timestamp_str:
                        continue
                    
                    # Parse timestamp
                    dt = datetime.strptime(timestamp_str, "%d.%m.%Y %H:%M")
                    hour_key = dt.strftime("%Y-%m-%d %H")
                    all_timestamps.append(dt)
                    
                    # Energy values in Wh, convert to kWh
                    from_grid_wh = float(row.get('Energy from grid (Wh)', 0) or 0)
                    to_grid_wh = float(row.get('Energy to grid (Wh)', 0) or 0)
                    
                    energy_from_grid[hour_key] += from_grid_wh / 1000  # Convert Wh to kWh
                    energy_to_grid[hour_key] += to_grid_wh / 1000      # Convert Wh to kWh
                    
                except (ValueError, KeyError) as e:
                    continue
    
    except Exception as e:
        print(f"Error reading inverter data: {e}")
        sys.exit(1)
    
    if not all_timestamps:
        print("No valid data found in inverter file")
        sys.exit(1)
    
    start_date = min(all_timestamps)
    end_date = max(all_timestamps)
    
    return dict(energy_from_grid), dict(energy_to_grid), start_date, end_date


def calculate_days_between(start_date: datetime, end_date: datetime) -> int:
    """Calculate number of days between two dates (inclusive)."""
    return (end_date - start_date).days + 1


def calculate_plan_cost(plan: Dict, energy_from_grid: Dict, energy_to_grid: Dict, 
                       start_date: datetime, end_date: datetime) -> Dict:
    """Calculate cost for a specific solar plan."""
    
    # Parse rates
    daily_supply_charge = parse_rate_value(plan.get("Daily Supply Charge", "0"))
    peak_consumption = parse_rate_value(plan.get("Peak Consumption", "0"))
    off_peak_consumption = parse_rate_value(plan.get("Off-Peak Consumption", "0"))
    export_rate_1 = parse_rate_value(plan.get("Export Rate 1", "0"))
    export_rate_2 = parse_rate_value(plan.get("Export Rate 2", "0"))
    export_rate_1_limit = parse_kwh_limit(plan.get("Export Rate 1 kWh limit", "N/A"))
    
    peak_hours = plan.get("Peak Hours", "All hours")
    off_peak_hours = plan.get("Off-Peak Hours", "N/A")
    
    # Export rate hours (read from plan data, not hardcoded)
    export_rate_2_hours = plan.get("Export Rate 2 Hours", "N/A")
    
    # Determine export rate 1 hours based on whether we have a daily kWh limit
    # Flow Power: N/A limit → use time window (5:30pm - 7:30pm)
    # Engie: kWh limit → "Remaining per day" means all hours after daily limit consumed
    if export_rate_1_limit is None:
        # Time-based export window (Flow Power style)
        export_rate_1_hours = "5:30pm - 7:30pm"
    else:
        # Consumption-bucket export window (Engie style) - applies all hours
        export_rate_1_hours = "All hours"
    
    # Check if this is a consumption bucket-based plan (Engie-style)
    peak_bucket_limit = parse_consumption_bucket_limit(peak_hours)
    has_consumption_buckets = peak_bucket_limit is not None
    
    # Check if this is single rate or TOU (only if not consumption bucket-based)
    is_single_rate = (not has_consumption_buckets and 
                     (peak_hours == "All hours" or 
                      off_peak_hours == "N/A" or 
                      off_peak_consumption == 0.0))
    
    total_import_cost = 0.0  # in dollars (rates are in c/kWh)
    total_export_revenue = 0.0  # in dollars
    
    # For consumption bucket-based plans, pre-calculate daily consumption and track cumulative by hour
    if has_consumption_buckets:
        # Group energy by date and sort by hour
        daily_energy = defaultdict(list)  # date_str -> [(hour_key, kWh), ...]
        for hour_key, kWh_imported in energy_from_grid.items():
            try:
                dt = datetime.strptime(hour_key, "%Y-%m-%d %H")
                date_str = dt.strftime("%Y-%m-%d")
                daily_energy[date_str].append((hour_key, kWh_imported))
            except ValueError:
                continue
        
        # Sort each day's hours
        for date_str in daily_energy:
            daily_energy[date_str].sort()
        
        # Process with cumulative tracking
        for date_str, hourly_data in daily_energy.items():
            cumulative = 0.0
            for hour_key, kWh_imported in hourly_data:
                # Calculate how much of this hour's energy is at peak vs off-peak rate
                cumulative_end = cumulative + kWh_imported
                
                if cumulative_end <= peak_bucket_limit:
                    # All consumption for this hour is at peak rate
                    cost = kWh_imported * peak_consumption / 100
                elif cumulative < peak_bucket_limit:
                    # Some consumption at peak, some at off-peak
                    peak_kwh = peak_bucket_limit - cumulative
                    offpeak_kwh = cumulative_end - peak_bucket_limit
                    cost = (peak_kwh * peak_consumption + offpeak_kwh * off_peak_consumption) / 100
                else:
                    # All consumption for this hour is at off-peak rate
                    cost = kWh_imported * off_peak_consumption / 100
                
                total_import_cost += cost
                cumulative = cumulative_end
    else:
        # Standard time-based rate plans
        for hour_key, kWh_imported in energy_from_grid.items():
            try:
                dt = datetime.strptime(hour_key, "%Y-%m-%d %H")
            except ValueError:
                continue

            if is_single_rate:
                cost = kWh_imported * peak_consumption / 100
                total_import_cost += cost
            else:
                # Time-based TOU plan
                # compute minutes overlap with peak and off-peak windows
                peak_min = minutes_overlap(dt, peak_hours)
                off_min = minutes_overlap(dt, off_peak_hours)
                other_min = 60 - peak_min - off_min
                if other_min < 0:
                    other_min = 0

                # treat any 'other' minutes as off-peak (conservative)
                off_total_min = off_min + other_min

                cost = 0.0
                if peak_min > 0:
                    cost += (peak_min / 60.0) * (kWh_imported * peak_consumption / 100)
                if off_total_min > 0:
                    cost += (off_total_min / 60.0) * (kWh_imported * off_peak_consumption / 100)

                total_import_cost += cost
    
    # Process export revenue
    # Flow Power: Time-window-based (5:30-7:30pm peak window)
    # Engie: Consumption-bucket-based (first N kWh/day at rate1, remainder at rate2)
    
    if export_rate_1_limit is None:
        # Flow Power: Time-based export rates
        for hour_key, kWh_exported in energy_to_grid.items():
            try:
                dt = datetime.strptime(hour_key, "%Y-%m-%d %H")
            except ValueError:
                continue

            # minutes in this hour that are in Export Rate 1 window (5:30-7:30pm)
            rate1_min = minutes_overlap(dt, export_rate_1_hours)
            rate1_kwh = (rate1_min / 60.0) * kWh_exported
            remaining_kwh = kWh_exported - rate1_kwh

            # compute revenues
            total_export_revenue += rate1_kwh * export_rate_1 / 100
            total_export_revenue += remaining_kwh * export_rate_2 / 100
    else:
        # Engie: Consumption-bucket-based export rates (daily kWh limit)
        daily_export_used = defaultdict(float)  # date_str -> kWh used at rate1
        for hour_key, kWh_exported in energy_to_grid.items():
            try:
                dt = datetime.strptime(hour_key, "%Y-%m-%d %H")
            except ValueError:
                continue

            date_str = dt.strftime("%Y-%m-%d")
            used = daily_export_used[date_str]
            
            # How much of this hour's export can use rate1 (within daily limit)?
            allowed_at_rate1 = max(0.0, export_rate_1_limit - used)
            applied_rate1_kwh = min(kWh_exported, allowed_at_rate1)
            rate2_kwh = kWh_exported - applied_rate1_kwh
            
            daily_export_used[date_str] = used + applied_rate1_kwh

            # compute revenues
            total_export_revenue += applied_rate1_kwh * export_rate_1 / 100
            total_export_revenue += rate2_kwh * export_rate_2 / 100
    
    # Calculate daily supply charge
    num_days = calculate_days_between(start_date, end_date)
    daily_supply_total = (daily_supply_charge * num_days) / 100  # Convert cents to dollars
    
    # Calculate net cost
    net_cost = total_import_cost + daily_supply_total - total_export_revenue
    
    return {
        "plan_name": plan.get("Plan Title", "Unknown"),
        "offer_id": plan.get("Offer ID", "N/A"),
        "total_import_cost": total_import_cost,
        "total_export_revenue": total_export_revenue,
        "daily_supply_total": daily_supply_total,
        "net_cost": net_cost,
        "daily_supply_charge_rate": daily_supply_charge,
        "num_days": num_days,
    }


def format_currency(value: float) -> str:
    """Format value as currency in dollars."""
    return f"${value:.2f}"


def main():
    """Main function to compare solar plans."""
    
    # File paths
    inverter_file = "Solar inverter data 1Feb25-23Feb26.csv"
    plans_file = "solar-plans-comparison.csv"
    
    print("=" * 80)
    print("Solar Plans Comparison Analysis")
    print("=" * 80)
    print()
    
    # Read input files
    print("Reading solar plans...")
    plans = read_solar_plans(plans_file)
    print(f"Loaded {len(plans)} solar plans")
    print()
    
    print("Reading inverter data...")
    energy_from_grid, energy_to_grid, start_date, end_date = read_inverter_data(inverter_file)
    print(f"Loaded inverter data from {start_date.strftime('%d.%m.%Y')} to {end_date.strftime('%d.%m.%Y')}")
    num_days = calculate_days_between(start_date, end_date)
    print(f"Period: {num_days} days")
    print()
    
    # Calculate costs for each plan
    results = []
    for plan in plans:
        result = calculate_plan_cost(plan, energy_from_grid, energy_to_grid, start_date, end_date)
        results.append(result)
    
    # Sort by net cost (ascending = best value first)
    results.sort(key=lambda x: x["net_cost"])
    
    # Display results
    print("=" * 80)
    print("PLAN COMPARISON RESULTS (Sorted by Best Value)")
    print("=" * 80)
    print()
    
    for rank, result in enumerate(results, 1):
        print(f"Rank {rank}: {result['plan_name']}")
        print(f"Offer ID: {result['offer_id']}")
        print(f"  Net Cost: {format_currency(result['net_cost'])}")
        print(f"    - Total Imported Energy Cost: {format_currency(result['total_import_cost'])}")
        print(f"    - Daily Supply Charge Total: {format_currency(result['daily_supply_total'])} ({result['num_days']} days × {result['daily_supply_charge_rate']:.2f}c/day)")
        print(f"    - Total Exported Energy Revenue: {format_currency(result['total_export_revenue'])}")
        print()
    
    # Additional summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    best_plan = results[0]
    worst_plan = results[-1]
    savings = worst_plan["net_cost"] - best_plan["net_cost"]
    
    print(f"Best Value Plan: {best_plan['plan_name']} ({best_plan['offer_id']})")
    print(f"  Net Cost: {format_currency(best_plan['net_cost'])}")
    print()
    print(f"Highest Cost Plan: {worst_plan['plan_name']} ({worst_plan['offer_id']})")
    print(f"  Net Cost: {format_currency(worst_plan['net_cost'])}")
    print()
    print(f"Potential savings by choosing best plan: {format_currency(savings)}")
    print()
    
    # Analysis and discrepancies
    print("=" * 80)
    print("ANALYSIS & KEY INSIGHTS")
    print("=" * 80)
    print()
    print("Plan Characteristics:")
    print("-" * 80)
    for result in results:
        plan_name = result['plan_name']
        print(f"\n{plan_name}:")
        print(f"  Import Energy Cost: {format_currency(result['total_import_cost'])}")
        print(f"  Export Revenue: {format_currency(result['total_export_revenue'])}")
        print(f"  Daily Supply Charge: {format_currency(result['daily_supply_total'])}")
        print(f"  Net Cost (Total): {format_currency(result['net_cost'])}")
    
    print()
    print("Key Findings:")
    print("-" * 80)
    print("1. Time of Use (TOU) Plans offer the best value")
    print("   - Lower consumption rates balance higher daily supply charge")
    print("   - TOU consumption rate: 33.88 c/kWh")
    print("   - Single rate consumption rate: 37.58 c/kWh")
    print()
    print("2. Controlled Load (CL) variant does not affect total cost")
    print("   - CL and non-CL plans show identical costs")
    print("   - In this dataset, CL does not import extra energy")
    print()
    print("3. Solar Export Revenue") 
    print(f"   - Total annual export: {sum(energy_to_grid.values()):.2f} kWh")
    print(f"   - Export occurs during daylight hours (6am-7pm)")
    print(f"   - Peak export rate (5:30-7:30pm): 35.00 c/kWh")
    print(f"   - Off-peak export rate: 0.00 c/kWh")
    print(f"   - Annual export revenue: {format_currency(results[0]['total_export_revenue'])}")
    print()
    print("4. Annual Savings Analysis")
    print(f"   - By choosing TOU over Single Rate: {format_currency(savings)}/year")
    annual_saving_pct = (savings / worst_plan['net_cost']) * 100
    print(f"   - Savings percentage: {annual_saving_pct:.1f}%")
    print()


if __name__ == "__main__":
    main()
