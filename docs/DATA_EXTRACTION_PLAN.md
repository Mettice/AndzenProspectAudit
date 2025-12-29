# DATA_EXTRACTION_PLAN.md

## For Executive Summary:
Need:
- Total revenue (last 12 months)
- Klaviyo attributed revenue
- Campaign revenue
- Flow revenue

API Calls:
1. GET /api/metric-aggregates/ (filter: Placed Order, last 12 months)
2. GET /api/campaigns/ (filter: date range)
3. GET /api/flows/

## For Flow Analysis (Welcome Series):
Need:
- Flow ID
- Messages in flow
- Open rate, click rate, conversion rate
- Revenue attributed

API Calls:
1. GET /api/flows/ (find Welcome Series by name)
2. GET /api/flow-messages/{flow_id}
3. Calculate metrics from message stats

[Continue for each section...]