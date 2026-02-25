---
name: compare-plans
description: Compares Solar inverter import/export power prices with different Solar plans
---
You are an analyst looking through a large CSV file of Solar inverter data, which includes import and export power prices. You also have a set of Solar plans with their respective import and export rates. 

Python script will be named `compare-solar-plans.py`.  Details on how to structure this script are below.

Your task is to create a Python script that reads in the CSV file `Solar inverter data 1Feb25-23Feb26.csv`, extracts the relevant import and export power prices, and compares them against the rates provided in the Solar plans.

The script should output a summary of how the inverter data aligns with each Solar plan, highlighting any discrepancies or advantages for each plan based on the imported and exported power prices.

# Solar plans
The solar plans are listed in the CSV file `solar-plans-comparison.csv`, which includes the following columns:
- Plan Name
- Daily Supply Charge (c/day)
- Peak Consumption (c/kWh)
- Peak Hours
- Off-Peak Consumption (c/kWh)
- Off-Peak Hours
- Export Rate 1 (c/kWh)
- Export Rate 1 Hours
- Export Rate 1 kWh limit
- Export Rate 2 (c/kWh)

If there are no Peak or Off-Peak consumption rates, they will be listed as "N/A".  A single rate will apply to all hours.

If there is an Export Rate 1 kWh limit, it will be listed as a number.  If there is no limit, it will be listed as "N/A".  If there is no Export Rate 1, it will be listed as "N/A".
The Export Rate 1 kWh limit is the maximum amount of energy that can be exported at Export Rate 1.  Any energy exported above this limit will be calculated at Export Rate 2.



# Inverter data
The inverter data in `Solar inverter data 1Feb25-23Feb26.csv` includes the following columns:
- Timestamp
- Energy from grid (Wh)
- Energy to grid (Wh)

The timestamp is in the format `DD.MM.YYYY hh:mm` in 24 hour time format.
The timestamps are every 5 minutes.  These need to be summed in to hourly data to compare with the Solar plans, which have hourly rates.

'Energy from grid (Wh)' is the amount of energy imported from the grid and will be calculated at the Peak or Off-Peak consumption rates depending on the time of day.

'Energy to grid (Wh)' is the amount of energy exported to the grid and will be calculated at the Export Rate 1 or Export Rate 2 depending on the time of day. Both values are in Watt-hours (Wh) and need to be converted to kilowatt-hours (kWh) for comparison with the Solar plans, which have rates in c/kWh.

To convert Wh to kWh, divide the value by 1000. For example, 500 Wh is equal to 0.5 kWh.

# Total cost
Based on a year's historical data, calculate the total cost of imported energy and the total revenue from exported energy for each Solar plan.


The total cost of the plan should be calculated as follows:
- Total Cost of Imported Energy = (Energy from grid during Peak Hours * Peak Consumption Rate) + (Energy from grid during Off-Peak Hours * Off-Peak Consumption Rate) in Dollars
- Daily Supply Charge multiplied by the number of days in the Inverter Data file (from the first date to the last date) in Dollars
- Minus Total Revenue from Exported Energy = (Energy to grid during Export Rate 1 Hours * Export Rate 1) in Dollars



# Output
The output should be a summary for each Solar plan, sorted by the best value plan based on the total cost of imported energy minus the total revenue from exported energy.


The summary should include:
- Plan Name
- Net cost (Imported Energy Cost + Daily Supply Charge - Exported Energy Revenue)
- Total Cost of Imported Energy (calculated using the Peak and Off-Peak consumption rates)
- Total Revenue from Exported Energy (calculated using the Export Rate 1 and Export Rate 2)
- Daily Supply Charge multiplied by the number of days in the Inverter Data file
- Any discrepancies or advantages for each plan based on the imported and exported power prices.

