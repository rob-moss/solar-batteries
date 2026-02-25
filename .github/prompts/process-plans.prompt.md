---
name: process-plans
description: Download solar plans in PDF format and output Markdown
---
Ingest the provided solar plans in PDF format, extract the relevant information, and output it in Markdown format for easy readability and further processing.

The URLs are contained in the Markdown file `solar-plan-urls.md`.
In this Markdown file there are multiple sections using Markdown headers, one for each power provider.

In this task, you need to look at all of the Heading sections, an extract all of the URLs contained in each secrion. Each URL points to a PDF document that contains the solar plans. Your task is to download each PDF, extract the necessary information, and convert it into a structured Markdown format.

Each URL points to a PDF document that contains the solar plans. Your task is to download each PDF, extract the necessary information, and convert it into a structured Markdown format. The PDF document contains some tables of data.


The working directory for temporary output, scripts and downloaded files is `./tmp`. You can create this directory if it does not exist. After processing, you can delete any temporary files created during the extraction process.


The PDF document contains some tables of data.
The relevant information to extract includes:
- The title of the plan, ie "Flow Power — Flow Home - Single Rate"
- The "Offer ID" ie "Offer ID: FLO719675MR"
- Fees, including:
  - "Disconnection fee"
  - "Reconnection fee"
  - "Payment processing fee"
- Billing details
- Offer rate and details, including:
  - "Daily supply charge"
  - "Peak consumption"
  - "Peak consumption hours"
  - "Off-Peak consumption"
  - "Off-Peak consumption hours"
  - "Export rate 1"
  - "Export rate 1 watts"
  - "Export rate 2"
- Any other relevant information that may be useful for comparing the plans

Export Rates are typically listed in the PDF as "Export rate 1" and "Export rate 2", along with the corresponding hours during which these rates apply. Make sure to extract both the rate and the hours for each export rate.
Export Rate 1 can sometimes include a set number of kWh that are paid at that rate, for example "First 8.000 kWh export per Day".  In this case, make sure to extract both the rate and the kWh limit for Export Rate 1.  The remainder of kWh exported that day will be calculated at Export Rate 2.


# Output

There are two output files to generate:
1. `solar-plans-extracted.md`: This file should contain the extracted information from the PDFs in a structured Markdown format, organized by plan.
2. `solar-plans-comparison.csv` : This file should contain a tabular comparison of the different plans in CSV format, using ',' comma to separate each field.


## Markdown Output Structure
The output should be in Markdown format, structured as follows:

```markdown
# Solar Plan: [Plan Title] Offer ID: [Offer ID]
- Fees:
  - Disconnection fee: [Disconnection fee]
  - Reconnection fee: [Reconnection fee]
  - Payment processing fee: [Payment processing fee]
- Billing details: [Billing details]

|| Daily Supply Charge | Peak Consumption | Peak Hours | Off-Peak Consumption | Off-Peak Hours | Off-Peak Hours | Export Rate 1 | Export Rate 1 Hours  Export Rate 1 kWh limit | Export Rate 2 | Export Rate 2 Hours ||
|---------------------|------------------|----------------------|---------------|-------------------|---------------|---------------|
| [Daily Supply Charge] | [Peak Consumption] | [Peak Hours] | [Off-Peak Consumption] | [Off-Peak Hours] | [Export Rate 1] | [Export Rate 1 Hours] | [Export Rate 1 kWh limit] | [Export Rate 2] | [Export Rate 2 Hours] |
```

Make sure to repeat this structure for each solar plan extracted from the PDFs. The output should be clear and organized, allowing for easy comparison between different plans.

## CSV Output Structure

The CSV file should have the following columns:
- Plan Title
- Offer ID
- Disconnection Fee
- Reconnection Fee
- Payment Processing Fee
- Daily Supply Charge
- Peak Consumption
- Peak Hours
- Off-Peak Consumption
- Off-Peak Hours
- Export Rate 1
- Export Rate 1 kWh limit (if applicable)
- Export Rate 2

The CSV file should also have a heading row with the column names.
The heading row should be the first row in the CSV file, followed by one row for each solar plan extracted from the PDFs, with the corresponding information in each column.
All CSV values should be quoted.
Each subsequent row should contain the corresponding information for each solar plan extracted from the PDFs.
