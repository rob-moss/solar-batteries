#!/usr/bin/env python3
"""
AER Energy Plan Fetcher

Queries the AER website API to fetch electricity plans and search for specific plan IDs.

Note: The AER API endpoint requires proper authentication and may have CORS restrictions.
If you encounter 400 errors, the API may require:
  - Authorization headers
  - API key
  - Specific request headers
  - CORS allowance from the client

Reference: https://cdr.energymadeeasy.gov.au/engie/cds-au/v1/energy/plans
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import urllib.parse


def _fetch_page(page):
    """Fetch a single page of energy plans from AER API (internal helper).
    
    Args:
        page: Page number to fetch
    
    Returns:
        Parsed JSON response or None if error
    """
    base_url = "https://cdr.energymadeeasy.gov.au/engie/cds-au/v1/energy/plans"
    params = {
        "type": "ALL",
        "fuelType": "ELECTRICITY",
        "effective": "ALL",
        "updated-since": "",
        "brand": "",
        "page-size": "100",
        "page": page
    }

    # Build URL with proper encoding
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"

    print(f"Fetching page {page} from AER API...")
    try:
        # Create request with headers
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        req.add_header('Accept', '*/*')
        req.add_header('Accept-Encoding', 'gzip, deflate, br')
        req.add_header('Connection', 'keep-alive')
        req.add_header('x-v', '1')
        req.add_header('x-v-min', '1')
        
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        if e.code == 400:
            print("  ⚠ API returned 400 Bad Request")
            print("  You may need to:")
            print("    - Check if the API requires authentication or API key")
            print("    - Review current AER API documentation")
            print("    - Check CORS settings if running from a browser context")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON response from server")
        return None
    except Exception as e:
        print(f"Error fetching plans: {e}")
        return None


def fetch_and_save_all_pages(output_file='aer-data-all-pages.json'):
    """Fetch all energy plans from all pages and save to JSON file.
    
    Args:
        output_file: Filename to save JSON output (default: 'aer-data-all-pages.json')
    
    Returns:
        Dictionary with all aggregated data, or None if error
    """
    print(f"Fetching all pages and saving to '{output_file}'...")
    print()
    
    # First, fetch page 1 to determine total number of pages
    print("Querying total number of pages...")
    first_page = _fetch_page(page=1)
    
    if not first_page:
        print("Failed to fetch first page")
        return None
    
    # Get pagination info from meta
    meta = first_page.get('meta', {})
    total_pages = meta.get('totalPages', 1)
    total_records = meta.get('totalRecords', 0)
    print(f"✓ Total pages available: {total_pages}")
    print(f"✓ Total records: {total_records}")
    print()
    
    # Collect all plans from all pages
    all_plans = []
    all_meta = meta
    all_links = first_page.get('links', {})
    
    print("Fetching all pages...")
    for page_num in range(1, total_pages + 1):
        print(f"  Fetching page {page_num}/{total_pages}...")
        
        # Fetch this page
        if page_num == 1:
            # We already have the first page
            data = first_page
        else:
            data = _fetch_page(page=page_num)
        
        if not data:
            print(f"    ✗ Failed to fetch page {page_num}")
            continue
        
        # Collect plans from this page
        plans = data.get('data', {}).get('plans', [])
        all_plans.extend(plans)
        print(f"    → Collected {len(plans)} plans (total so far: {len(all_plans)})")
    
    # Prepare output data in same format as API
    output_data = {
        'data': {
            'plans': all_plans
        },
        'meta': all_meta,
        'links': all_links
    }
    
    # Save to JSON file
    try:
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print()
        print(f"✓ Successfully saved {len(all_plans)} plans to '{output_file}'")
        return output_data
    except Exception as e:
        print(f"✗ Error saving to file: {e}")
        return None


def fetch_plan_details(plan_id):
    """Fetch detailed plan information for a specific plan ID.
    
    Queries the AER API endpoint with the plan_id appended to get comprehensive
    plan details including pricing, fees, and terms. Returns structured data
    similar to solar-plans-comparison.csv format.
    
    Args:
        plan_id: The plan ID to fetch details for (e.g., 'ENG718282MR@VEC')
    
    Returns:
        Dictionary with plan details including:
            - planId: Plan identifier
            - displayName: Plan name/title
            - dailySupplyCharge: Daily supply charge
            - peakConsumptionRate: Peak consumption rate
            - offPeakConsumptionRate: Off-peak consumption rate
            - peakHours: Hours when peak rates apply
            - offPeakHours: Hours when off-peak rates apply
            - exportRate: Export rate (c/kWh)
            - exportLimit: Daily export limit (kWh)
            - fees: Dict with disconnection, reconnection, payment fees
            - full_response: Complete API JSON response
        None if error
    """
    print(f"Fetching plan details for: {plan_id}")
    
    base_url = "https://cdr.energymadeeasy.gov.au/engie/cds-au/v1/energy/plans"
    url = f"{base_url}/{plan_id}"
    
    print(f"URL: {url}")
    print()
    
    try:
        # Create request with headers
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        req.add_header('Accept', 'application/json')
        req.add_header('Accept-Encoding', 'gzip, deflate, br')
        req.add_header('Connection', 'keep-alive')
        req.add_header('x-v', '3')
        req.add_header('x-v-min', '1')
        
        with urlopen(req, timeout=10) as response:
            raw_data = json.loads(response.read().decode('utf-8'))
            
            # Extract plan details from response
            plan_data = raw_data.get('data', {})
            
            # Parse pricing information: some plans use `electricityContract` (ENGIE example)
            # while others use a top-level `pricing` object. Prefer electricityContract.
            pricing = plan_data.get('pricing', {})
            contract = plan_data.get('electricityContract') or pricing or {}

            # Extract consumption rates: try electricityContract.tariffPeriod[*].singleRate.rates
            electricity_rates = []
            tp = contract.get('tariffPeriod') if isinstance(contract.get('tariffPeriod'), list) else contract.get('tariffPeriod')
            if tp:
                first_tp = tp[0] if isinstance(tp, list) and tp else tp
                # Look for singleRate or singleRate equivalent
                sr = first_tp.get('singleRate') or first_tp.get('singleRate')
                if sr and isinstance(sr, dict):
                    electricity_rates = sr.get('rates', [])
                else:
                    # Fallback: check for rate blocks named 'rates' at the tariffPeriod level
                    electricity_rates = first_tp.get('rates', []) if isinstance(first_tp.get('rates', []), list) else []
            # Final fallback: pricing.electricity[*].rates
            if not electricity_rates and pricing:
                rate_details = pricing.get('electricity', [])
                if rate_details:
                    electricity_rates = rate_details[0].get('rates', []) if isinstance(rate_details, list) else rate_details.get('rates', [])

            # Extract fees: support both electricityContract.fees and pricing.fees
            fees_source = contract.get('fees') or pricing.get('fees') or []
            fee_dict = {}
            for fee in fees_source:
                # Common keys observed: 'type' or 'feeType', amount in 'amount' or 'rate'
                fee_key = fee.get('type') or fee.get('feeType') or fee.get('term') or fee.get('description')
                fee_amount = fee.get('amount') or fee.get('rate') or fee.get('value')
                if fee_key:
                    fee_dict[fee_key] = fee_amount
            
            # Determine daily supply charge robustly. Prefer electricityContract.tariffPeriod
            # (example: electricityContract.tariffPeriod[0].dailySupplyCharge) and
            # fall back to pricing.electricity[*].supplyChargeAmount or dailySupplyCharge.
            daily_supply = 'N/A'
            # Try electricityContract -> tariffPeriod
            elec_contract = plan_data.get('electricityContract', {}) or {}
            tp = elec_contract.get('tariffPeriod') if isinstance(elec_contract.get('tariffPeriod'), list) else elec_contract.get('tariffPeriod')
            if tp:
                first_tp = tp[0] if isinstance(tp, list) and tp else tp
                dsc = first_tp.get('dailySupplyCharge') or first_tp.get('supplyChargeAmount')
                if dsc:
                    daily_supply = dsc
            # Fallback to pricing.electricity
            if daily_supply == 'N/A' and pricing:
                elec = pricing.get('electricity')
                if elec:
                    first = elec[0] if isinstance(elec, list) and elec else elec
                    dsc = first.get('supplyChargeAmount') or first.get('dailySupplyCharge')
                    if dsc:
                        daily_supply = dsc

            # solarFeedInTariff
            # solarFeedInTariff
            # Map solarFeedInTariff.singleTariff.rates to export fields:
            #  - singleTariff.rates[0].volume => Export Rate 1 kWh limit
            #  - singleTariff.rates[0].unitPrice => Export Rate 1
            #  - singleTariff.rates[1].unitPrice => Export Rate 2
            export_rate_1_limit = None
            export_rate_1 = None
            export_rate_2 = None
            solar_fit_raw = None

            # look in electricityContract first (example data present there)
            sfit = elec_contract.get('solarFeedInTariff') if isinstance(elec_contract, dict) else None
            if not sfit:
                # fallback to pricing
                sfit = pricing.get('solarFeedInTariff') if isinstance(pricing, dict) else None

            if sfit:
                solar_fit_raw = sfit
                first_fit = sfit[0] if isinstance(sfit, list) and sfit else sfit
                st = first_fit.get('singleTariff') or first_fit.get('singleTariff')
                if st and isinstance(st, dict):
                    rates = st.get('rates', [])
                    if isinstance(rates, list) and len(rates) > 0:
                        r0 = rates[0]
                        export_rate_1_limit = r0.get('volume')
                        export_rate_1 = r0.get('unitPrice')
                        # try convert to cents if numeric
                        try:
                            export_rate_1_c = int(float(export_rate_1) * 100) if export_rate_1 is not None else None
                        except Exception:
                            export_rate_1_c = None
                        if len(rates) > 1:
                            r1 = rates[1]
                            export_rate_2 = r1.get('unitPrice')
                            try:
                                export_rate_2_c = int(float(export_rate_2) * 100) if export_rate_2 is not None else None
                            except Exception:
                                export_rate_2_c = None
                        else:
                            export_rate_2_c = None
                    else:
                        export_rate_1_c = None
                        export_rate_2_c = None
                else:
                    export_rate_1_c = None
                    export_rate_2_c = None
            else:
                export_rate_1_c = None
                export_rate_2_c = None

            # Structure output similar to CSV format
            structured_data = {
                'planId': plan_data.get('planId', plan_id),
                'displayName': plan_data.get('displayName', 'N/A'),
                'brand': plan_data.get('brand', 'N/A'),
                'description': plan_data.get('description', ''),
                'dailySupplyCharge': daily_supply,
                'electricityRates': electricity_rates,
                'fees': fee_dict,
                'solarFeedInTariff': solar_fit_raw,
                'export_rate_1_kwh_limit': export_rate_1_limit,
                'export_rate_1_unitPrice': export_rate_1,
                'export_rate_1_c_per_kwh': export_rate_1_c if 'export_rate_1_c' in locals() else None,
                'export_rate_2_unitPrice': export_rate_2,
                'export_rate_2_c_per_kwh': export_rate_2_c if 'export_rate_2_c' in locals() else None,
                'terms': plan_data.get('terms', {}),
                'full_response': raw_data
            }
            
            print(f"✓ Successfully fetched plan details for {plan_id}")
            return structured_data
            
    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        if e.code == 404:
            print(f"  Plan '{plan_id}' not found (404)")
        elif e.code == 400:
            print("  API returned 400 Bad Request")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON response from server")
        return None
    except Exception as e:
        print(f"Error fetching plan details: {e}")
        return None


def search_plan_by_id(plan_id):
    """Search for a plan by planId by looping through all pages.
    
    First queries to determine total pages, then loops through each page
    until the plan is found.
    
    Args:
        plan_id: The plan ID to search for (e.g., 'ENG718282MR')
    
    Returns:
        Plan data if found, None otherwise
    """
    print(f"Searching for plan ID: {plan_id}")
    print()
    
    # First, fetch page 1 to determine total number of pages
    print("Querying total number of pages...")
    first_page = _fetch_page(page=1)
    
    if not first_page:
        print("Failed to fetch first page")
        return None
    
    # Get pagination info from meta
    meta = first_page.get('meta', {})
    total_pages = meta.get('totalPages', 1)
    total_records = meta.get('totalRecords', 0)
    print(f"✓ Total pages available: {total_pages}")
    print(f"✓ Total records: {total_records}")
    print()
    
    # Loop through each page looking for the plan
    print("Looping through pages to find plan...")
    for page_num in range(1, total_pages + 1):
        print(f"  Checking page {page_num}/{total_pages}...")
        
        # Fetch this page
        if page_num == 1:
            # We already have the first page
            data = first_page
        else:
            data = _fetch_page(page=page_num)
        
        if not data:
            print(f"    Failed to fetch page {page_num}")
            continue
        
        # Search for the plan on this page
        plans = data.get('data', {}).get('plans', [])
        print(f"    → Checking {len(plans)} plans on this page")
        
        for plan in plans:
            if plan.get('planId') == plan_id:
                print(f"✓ Found plan: {plan_id} on page {page_num}")
                return plan
    
    print(f"✗ Plan '{plan_id}' not found after checking all {total_pages} pages")
    return None


def display_plan(plan):
    """Display plan information in a readable format."""
    if not plan:
        print("No plan found")
        return
    
    print("\n" + "=" * 80)
    print("PLAN DETAILS")
    print("=" * 80)
    print(f"Plan ID: {plan.get('planId', 'N/A')}")
    print(f"Plan Name: {plan.get('displayName', 'N/A')}")
    print(f"Brand: {plan.get('brand', 'N/A')}")
    print(f"Fuel Type: {plan.get('fuelType', 'N/A')}")
    print(f"Offer URL: {plan.get('offerUri', 'N/A')}")
    print(f"Effective From: {plan.get('effectiveFrom', 'N/A')}")
    print(f"Last Updated: {plan.get('lastUpdated', 'N/A')}")
    print(f"Comparison Rate: {plan.get('comparisonRate', 'N/A')}")
    print(f"Cooling Off Days: {plan.get('coolingOffDays', 'N/A')}")
    
    # Display pricing information if available
    if 'pricing' in plan:
        pricing = plan['pricing']
        print("\nPRICING:")
        print(json.dumps(pricing, indent=2))
    
    # Display export / solar feed-in tariff details if present
    # Prefer structured fields added by fetch_plan_details(), else search common JSON paths
    if any(k in plan for k in ('export_rate_1_kwh_limit', 'export_rate_1_unitPrice', 'export_rate_2_unitPrice')):
        print("\nEXPORT RATES (structured):")
        print(f"Export Rate 1 kWh limit: {plan.get('export_rate_1_kwh_limit')}")
        print(f"Export Rate 1 unitPrice: {plan.get('export_rate_1_unitPrice')}")
        if plan.get('export_rate_1_c_per_kwh') is not None:
            print(f"Export Rate 1 (c/kWh): {plan.get('export_rate_1_c_per_kwh')}")
        print(f"Export Rate 2 unitPrice: {plan.get('export_rate_2_unitPrice')}")
        if plan.get('export_rate_2_c_per_kwh') is not None:
            print(f"Export Rate 2 (c/kWh): {plan.get('export_rate_2_c_per_kwh')}")
    else:
        # search common locations for solarFeedInTariff
        sfit = None
        # check nested places where data might appear
        candidates = []
        if isinstance(plan.get('full_response'), dict):
            candidates.append(plan['full_response'].get('data'))
        if isinstance(plan.get('data'), dict):
            candidates.append(plan.get('data'))
        if isinstance(plan.get('electricityContract'), dict):
            candidates.append(plan.get('electricityContract'))
        if isinstance(plan.get('pricing'), dict):
            candidates.append(plan.get('pricing'))

        for c in candidates:
            if not c:
                continue
            if isinstance(c, dict) and 'solarFeedInTariff' in c:
                sfit = c.get('solarFeedInTariff')
                break

        if sfit:
            first_fit = sfit[0] if isinstance(sfit, list) and sfit else sfit
            st = first_fit.get('singleTariff') if isinstance(first_fit, dict) else None
            rates = st.get('rates', []) if isinstance(st, dict) else []
            print("\nEXPORT RATES (solarFeedInTariff):")
            if rates and isinstance(rates, list):
                if len(rates) > 0:
                    r0 = rates[0]
                    print(f"Export Rate 1 kWh limit: {r0.get('volume')}")
                    print(f"Export Rate 1 unitPrice: {r0.get('unitPrice')}")
                    try:
                        print(f"Export Rate 1 (c/kWh): {int(float(r0.get('unitPrice')) * 100)}")
                    except Exception:
                        pass
                if len(rates) > 1:
                    r1 = rates[1]
                    print(f"Export Rate 2 unitPrice: {r1.get('unitPrice')}")
                    try:
                        print(f"Export Rate 2 (c/kWh): {int(float(r1.get('unitPrice')) * 100)}")
                    except Exception:
                        pass
            else:
                print("No rates array found in solarFeedInTariff")
        else:
            print("\nNo solar feed-in tariff / export rate data found")

    # Display full plan data as JSON
    print("\nFULL PLAN DATA (JSON):")
    print(json.dumps(plan, indent=2))
    print("=" * 80)


def main():
    """Main function."""
    plan_id = "ENG718282MR"
    
    print("=" * 80)
    print("AER Energy Plan Fetcher")
    print("=" * 80)
    print()
    
    # First, fetch all pages and export to JSON
    all_data = fetch_and_save_all_pages('aer-data-all-pages.json')
    
    if not all_data:
        print("\n✗ Failed to fetch and save plan data")
        return 1
    
    print()
    print("=" * 80)
    print()
    
    # Then search for the specific plan in the fetched data
    print(f"Searching for plan ID: {plan_id}")
    plans = all_data.get('data', {}).get('plans', [])
    
    for plan in plans:
        # Extract base plan ID (before @ delimiter) and compare
        full_plan_id = plan.get('planId', '')
        base_plan_id = full_plan_id.split('@')[0]
        
        if base_plan_id == plan_id:
            print(f"✓ Found plan: {plan_id} (full ID: {full_plan_id})")
            display_plan(plan)
            
            # Now fetch detailed plan information using the full plan ID
            print()
            print("=" * 80)
            print("Fetching detailed plan information from specific endpoint...")
            print("=" * 80)
            print()
            
            plan_details = fetch_plan_details(full_plan_id)
            if plan_details:
                print()
                print("PLAN DETAILS (Structured format):")
                print("-" * 80)
                print(f"Plan ID: {plan_details.get('planId', 'N/A')}")
                print(f"Display Name: {plan_details.get('displayName', 'N/A')}")
                print(f"Brand: {plan_details.get('brand', 'N/A')}")
                print(f"Daily Supply Charge: {plan_details.get('dailySupplyCharge', 'N/A')}")
                print(f"Electricity Rates: {json.dumps(plan_details.get('electricityRates', []), indent=2)}")
                print(f"Fees: {json.dumps(plan_details.get('fees', {}), indent=2)}")
                # Export / solar feed-in tariff details
                print()
                print("EXPORT DETAILS:")
                sfit = plan_details.get('solarFeedInTariff')
                if sfit:
                    try:
                        print("Solar Feed-In Tariff (raw):")
                        print(json.dumps(sfit, indent=2))
                    except Exception:
                        print(f"solarFeedInTariff: {sfit}")

                er_limit = plan_details.get('export_rate_1_kwh_limit')
                er1 = plan_details.get('export_rate_1_unitPrice')
                er1_c = plan_details.get('export_rate_1_c_per_kwh')
                er2 = plan_details.get('export_rate_2_unitPrice')
                er2_c = plan_details.get('export_rate_2_c_per_kwh')

                print(f"Export Rate 1 kWh limit: {er_limit}")
                print(f"Export Rate 1 unitPrice: {er1}")
                if er1_c is not None:
                    print(f"Export Rate 1 (c/kWh): {er1_c}")
                print(f"Export Rate 2 unitPrice: {er2}")
                if er2_c is not None:
                    print(f"Export Rate 2 (c/kWh): {er2_c}")
            
            return 0
    
    print(f"✗ Plan '{plan_id}' not found in {len(plans)} available plans")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
