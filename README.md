# Solar Power plans and Solar Batteries

This repository has been created as a project to provide in depth calculations for Home solar power generation and Grid power pricing.


# How it is calculated
There are a few main factors at play when calculating the best value electricity plan
* Daily supply charge - this can range between 80c to $1.40 per day, multipled by every day
* Peak power charge - this can be between 30-50c depending on the retailer, between certain hours of the day
* Off-Peak power charge - this can be beteeen 20-40c depending on the retailer.

The overall cost of a solar plan for a year is as follows:  
(Daily supply charge) + ( Peak power in Peak Hour window ) + (Off-Peak power) - (Solar FiT)


# How to use this
The overall method is
* Log in to your home power meter or inverter and download 5 minute or hourly power usage data including.
* Save the power data as a CSV file.  The example file `Solar inverter data 1Feb25-23Feb26.csv` contains a year's worth of power data in 5 minute intervals.
* Run the prompt `process-plans` to pull down the latest electricity supplier plans from their published PDFs available as URLs
* Use the python script `compare-solar-plans.py` to compare the Inverter data power draw from the grid at peak/offpeak time and the solar FiT

