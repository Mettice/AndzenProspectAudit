# Morrison Audit Blueprint - Complete Specification

> **Master Reference Document for Audit Report System Rebuild**
> 
> This document defines the complete structure, data requirements, and styling specifications
> needed to generate professional audit reports matching the Morrison/Andzen standard.

---

## Table of Contents

1. [Report Overview](#1-report-overview)
2. [Page-by-Page Specification](#2-page-by-page-specification)
3. [Data Requirements](#3-data-requirements)
4. [Benchmark Specifications](#4-benchmark-specifications)
5. [Visual Components](#5-visual-components)
6. [Template Module Structure](#6-template-module-structure)
7. [CSS Styling Guide](#7-css-styling-guide)

---

## 1. Report Overview

### 1.1 Document Properties

| Property | Value |
|----------|-------|
| Total Pages | 18 |
| Format | A4 Portrait |
| Brand | Andzen |
| Title | "Customer Journey Marketing: Audit Insights" |
| Time Period | 90 Days (default) |

### 1.2 Section Summary

| Page(s) | Section Name | Template Module |
|---------|--------------|-----------------|
| 1 | Cover Page | `cover.html` |
| 2-3 | KAV Analysis | `kav_analysis.html` |
| 4 | List Growth | `list_growth.html` |
| 5-6 | Data Capture | `data_capture.html` |
| 7 | Automation Performance Overview | `automation_overview.html` |
| 8 | Welcome Series Deep Dive | `flow_welcome.html` |
| 9-10 | Abandoned Cart Deep Dive | `flow_abandoned_cart.html` |
| 11 | Browse Abandonment Deep Dive | `flow_browse_abandonment.html` |
| 12-13 | Post Purchase & Strategies | `flow_post_purchase.html` |
| 14 | Okendo Reviews Flows | `advanced_reviews.html` |
| 15-16 | Wishlist Automation | `advanced_wishlist.html` |
| 17 | Campaign Performance | `campaign_performance.html` |
| 18 | Segmentation Strategy | `segmentation_strategy.html` |

---

## 2. Page-by-Page Specification

### PAGE 1: Cover Page
**Template**: `sections/cover.html`

#### Content Structure
```
┌─────────────────────────────────────────┐
│         [Andzen Green Brush Logo]       │
│                                         │
│            [CLIENT LOGO/NAME]           │
│              (Large, Bold)              │
│                                         │
│     Customer Journey Marketing:         │
│          Audit Insights                 │
│                                         │
│  ┌─────────────────┬──────────────────┐ │
│  │ Client Name     │ {{ client_name }}│ │
│  ├─────────────────┼──────────────────┤ │
│  │ Andzen Code     │ {{ client_code }}│ │
│  ├─────────────────┼──────────────────┤ │
│  │ Audit Date      │ {{ audit_date }} │ │
│  ├─────────────────┼──────────────────┤ │
│  │ Audit by        │ {{ auditor }}    │ │
│  └─────────────────┴──────────────────┘ │
│                                         │
│         [Andzen Logo Footer]            │
└─────────────────────────────────────────┘
```

#### Data Required
```python
cover_data = {
    "client_name": str,       # "Morrison"
    "client_code": str,       # "MRISON"
    "audit_date": str,        # "24 Feb 2024"
    "auditor_name": str,      # "Carissa Tumala"
    "client_logo_url": str    # Optional
}
```

---

### PAGE 2-3: KAV Analysis
**Template**: `sections/kav_analysis.html`

#### Section Title
"KAV: YOUR KLAVIYO TOTAL REVENUE (90 DAYS)"

#### Content Structure
```
┌─────────────────────────────────────────┐
│ KAV: YOUR KLAVIYO TOTAL REVENUE (90 DAYS)│
├─────────────────────────────────────────┤
│ Total Website Revenue in the 90 Days    │
│ (November 26, 2023 - February 24, 2024) │
├─────────────────────────────────────────┤
│ Growth overview                         │
│                                         │
│ A$1,014,093.54        [REVENUE CHART]   │
│ Total revenue                           │
│ ↗ 78.4% vs. previous 90 days           │
│                                         │
│ Attributed revenue: A$343K (33.81%)     │
│ ↗ 45.3%                                │
├─────────────────────────────────────────┤
│ REVENUE BREAKDOWN TABLE                 │
│ ┌────────────┬────────────┬────────────┐│
│ │Total       │Klaviyo     │Flow        ││
│ │Website     │Attributed  │Attributed  ││
│ │Revenue     │Revenue     │Revenue     ││
│ ├────────────┼────────────┼────────────┤│
│ │$1,014,093  │$343k       │$220,963    ││
│ └────────────┴────────────┴────────────┘│
├─────────────────────────────────────────┤
│ [Strategic narrative paragraph about    │
│  KAV performance and opportunities]     │
└─────────────────────────────────────────┘
```

#### Data Required
```python
kav_data = {
    "period": {
        "start_date": str,    # "November 26, 2023"
        "end_date": str,      # "February 24, 2024"
        "days": int           # 90
    },
    "revenue": {
        "total_website": float,          # 1014093.54
        "total_website_formatted": str,  # "A$1,014,093.54"
        "vs_previous_period": float,     # 78.4 (percentage)
        "attributed": float,             # 343000
        "attributed_percentage": float,  # 33.81
        "attributed_vs_previous": float, # 45.3
        "flow_attributed": float,        # 220963.82
        "campaign_attributed": float     # 121884.93
    },
    "chart_data": {
        "labels": ["Nov 1", "Dec 1", "Jan 1", "Feb 1"],
        "attributed_revenue": [100000, 200000, 280000, 343000],
        "unattributed_revenue": [150000, 250000, 350000, 451000],
        "total_recipients": [50000, 150000, 301000, 451000]
    },
    "narrative": str  # Strategic analysis paragraph
}
```

#### Revenue Table Columns
| Column | Header Text | Data Key |
|--------|-------------|----------|
| 1 | Total Website Revenue | `total_website` |
| 2 | Total Klaviyo-Attributed Revenue | `attributed` |
| 3 | Total Flow-Attributed Revenue | `flow_attributed` |
| 4 | Total Campaign-Attributed Revenue | `campaign_attributed` |

---

### PAGE 4: List Growth
**Template**: `sections/list_growth.html`

#### Section Title
"LIST GROWTH"

#### Content Structure
```
┌─────────────────────────────────────────┐
│              LIST GROWTH                │
├─────────────────────────────────────────┤
│ [Introductory paragraph about list      │
│  being analyzed and time period]        │
├──────────────────┬──────────────────────┤
│ LIST SIZE CHART  │ NET MEMBERSHIP CHART │
│                  │                      │
│ 2,673            │ 2,673                │
│ Total members    │ Net membership change│
│ [Bar chart]      │ [Bar chart]          │
├──────────────────┴──────────────────────┤
│ Based on the data provided, your list   │
│ grew by 2,741 subscribers during the    │
│ specified time period and a significant │
│ 44.22% of the new sign-ups seem to      │
│ originate from your popup form while    │
│ 41.70% of the new profiles originated   │
│ from your footer form.                  │
│                                         │
│ During the same period, there was a     │
│ loss of 65 subscribers due to spam      │
│ complaints, bounces and unsubscribed    │
│ individuals, but this only represents   │
│ approximately 2.37% of your new sign-ups│
│                                         │
│ While a churn rate of 2.37% may appear  │
│ healthy...                              │
└─────────────────────────────────────────┘
```

#### Data Required
```python
list_growth_data = {
    "list_name": str,           # "Morrison"
    "period_months": int,       # 6
    "current_total": int,       # 2673
    "net_change": int,          # 2673
    "growth_subscribers": int,  # 2741
    "lost_subscribers": int,    # 65
    "churn_rate": float,        # 2.37
    "signup_sources": {
        "popup_form": float,    # 44.22
        "footer_form": float,   # 41.70
        "other": float          # 14.08
    },
    "chart_data": {
        "months": ["Sep 23", "Oct 23", "Nov 23", "Dec 23", "Jan 24", "Feb 24"],
        "total_members": [0, 200, 800, 1600, 2200, 2673],
        "net_change": [-100, 200, 600, 800, 600, 473]
    },
    "analysis_text": str  # Generated narrative
}
```

---

### PAGE 5-6: Data Capture
**Template**: `sections/data_capture.html`

#### Section Title
"DATA CAPTURE"

#### Form Performance Table Structure
```
┌────────────────┬──────┬────────────┬──────────┬────────┬──────────┐
│ Name of Form   │ Type │Impressions │Total     │Submit  │Standing  │
│                │      │            │Submitted │Rate    │          │
├────────────────┼──────┼────────────┼──────────┼────────┼──────────┤
│Subscriber Pop-up│Popup │    81k     │   826    │ 0.9%   │  Poor    │
│Newsletter Footer│Embed │    1.3M    │   1.2k   │ 0.10%  │  Poor    │
│Subscriber Embed │Embed │    110     │   65     │59.09%  │Excellent │
│VIP SMS Sale    │Embed │    22      │   6      │27.27%  │Excellent │
│Access Embed    │      │            │          │        │          │
└────────────────┴──────┴────────────┴──────────┴────────┴──────────┘
```

#### Data Required
```python
data_capture_data = {
    "forms": [
        {
            "name": str,           # "Subscriber Pop-up"
            "type": str,           # "Popup" | "Embed"
            "impressions": int,    # 81000
            "impressions_fmt": str,# "81k"
            "submitted": int,      # 826
            "submitted_fmt": str,  # "826"
            "submit_rate": float,  # 0.9
            "standing": str        # "Poor" | "Average" | "Good" | "Excellent"
        }
    ],
    "analysis": {
        "popup_timing": str,       # "triggers after just 12 seconds"
        "recommended_timing": str, # "at least 20 seconds"
        "cta_feedback": str        # Analysis of call-to-action
    },
    "advanced_targeting": [
        "Exit Intent",
        "Returning Customer Form",
        "Engaged With Form But Not Submitted",
        "Idle Cart",
        "Page Views",
        "Product Viewed"
    ],
    "progressive_profiling": {
        "enabled": bool,
        "description": str
    },
    "flyout_forms": {
        "enabled": bool,
        "description": str
    }
}
```

#### Standing Criteria
| Submit Rate | Standing |
|-------------|----------|
| < 1% | Poor |
| 1-3% | Average |
| 3-10% | Good |
| > 10% | Excellent |

---

### PAGE 7: Automation Performance Overview
**Template**: `sections/automation_overview.html`

#### Section Title
"OVERALL AUTOMATION PERFORMANCE (90 DAYS)"

#### Email Automation Table Structure
```
┌───────────────────┬────────┬────────┬────────┬─────────┬─────────┐
│ Flow Name         │Avg Open│Avg     │Avg     │Revenue  │Revenue  │
│                   │Rate    │Click   │Placed  │Per      │         │
│                   │        │Rate    │Order   │Recipient│         │
│                   │        │        │Rate    │         │         │
├───────────────────┼────────┼────────┼────────┼─────────┼─────────┤
│Welcome Series     │ 71.19% │ 21.20% │ 11.64% │$73,866  │ $39.35  │
│Abandoned Checkout │ 62.20% │ 16.33% │ 6.42%  │$25,343  │ $20.83  │
│Abandoned Cart     │ 62.56% │ 11.17% │ 1.40%  │$15,050  │ $3.98   │
│Reminder           │        │        │        │         │         │
│Back In Stock Flow │ 69.15% │ 34.21% │ 9.97%  │$7,570   │ $27.86  │
└───────────────────┴────────┴────────┴────────┴─────────┴─────────┘
```

#### Data Required
```python
automation_overview_data = {
    "period_days": int,  # 90
    "flows": [
        {
            "name": str,                    # "Welcome Series"
            "avg_open_rate": float,         # 71.19
            "avg_click_rate": float,        # 21.20
            "avg_placed_order_rate": float, # 11.64
            "revenue": float,               # 73866.58
            "revenue_per_recipient": float  # 39.35
        }
    ],
    "summary": {
        "total_conversion_value": float,    # 122494.98
        "vs_previous_period": float,        # 96.7
        "total_recipients": int,            # 7848
        "recipients_vs_previous": float     # 116.1
    },
    "chart_data": {
        "months": ["Nov 1", "Dec 1", "Jan 1", "Feb 1"],
        "conversion_value": [10000, 20000, 30000, 40000],
        "total_recipients": [648, 1300, 1900, 2590]
    },
    "narrative": str  # Performance analysis
}
```

---

### PAGE 8: Welcome Series Deep Dive
**Template**: `sections/flow_welcome.html`

#### Section Title
"NURTURE / WELCOME SERIES"

#### Content Structure
```
┌─────────────────────────────────────────┐
│        NURTURE / WELCOME SERIES         │
├─────────────────────────────────────────┤
│ [Introductory paragraph about welcome   │
│  series importance and purpose]         │
├─────────────────────────────────────────┤
│ Welcome Flow Performance in last 90 Days│
│ ┌─────────────────────────────────────┐ │
│ │ EMAIL AUTOMATION (Green Header)     │ │
│ ├────────┬────────┬────────┬──────────┤ │
│ │Flow    │Avg Open│Avg     │Revenue   │ │
│ │Name    │Rate    │Click   │Per Recip │ │
│ ├────────┼────────┼────────┼──────────┤ │
│ │Welcome │ 71.19% │ 21.20% │ $39.35   │ │
│ │Series  │        │        │          │ │
│ └────────┴────────┴────────┴──────────┘ │
├─────────────────────────────────────────┤
│ What does "good" look like for a        │
│ welcome series (Apparel and Accessories)│
│ ┌─────────────────────────────────────┐ │
│ │ Flow Name │Open   │Click │Conv│RPR │ │
│ │           │Rate   │Rate  │Rate│    │ │
│ ├───────────┼───────┼──────┼────┼────┤ │
│ │ Welcome   │59.07% │5.70% │2.52│$3.11│ │
│ │ Series    │       │      │ %  │    │ │
│ └───────────┴───────┴──────┴────┴────┘ │
├─────────────────────────────────────────┤
│ [Performance analysis and recommendations│
│  - mentions 2 emails in flow            │
│  - 23-day gap analysis                  │
│  - expansion recommendations]           │
└─────────────────────────────────────────┘
```

#### Data Required
```python
welcome_flow_data = {
    "flow_name": "Welcome Series",
    "status": str,              # "live" | "draft" | "manual"
    "email_count": int,         # 2
    "performance": {
        "open_rate": float,     # 71.19
        "click_rate": float,    # 21.20
        "placed_order_rate": float,  # 11.64
        "revenue": float,       # 73866.58
        "revenue_per_recipient": float  # 39.35
    },
    "benchmark": {
        "open_rate": float,     # 59.07
        "click_rate": float,    # 5.70
        "conversion_rate": float,  # 2.52
        "revenue_per_recipient": float  # 3.11
    },
    "vs_benchmark": {
        "open_rate_diff": float,    # +12.12pp
        "click_rate_diff": float,   # +15.50pp
        "status": str               # "exceeds" | "meets" | "below"
    },
    "analysis": {
        "email_gap_days": int,      # 23
        "recommendations": [str]
    }
}
```

---

### PAGE 9-10: Abandoned Cart Deep Dive
**Template**: `sections/flow_abandoned_cart.html`

#### Section Title
"ABANDONED CART & ADD TO CART"

#### Data Required
```python
abandoned_cart_data = {
    "flows": [
        {
            "name": str,        # "Abandoned Checkout - Started Checkout Trigger"
            "open_rate": float,
            "click_rate": float,
            "placed_order_rate": float,
            "revenue_per_recipient": float,
            "revenue": float
        },
        {
            "name": str,        # "Abandoned Cart Reminder - Added to Cart Trigger"
            # ... same metrics
        }
    ],
    "benchmark": {
        "name": "Abandoned Cart",
        "open_rate": 54.74,
        "click_rate": 6.25,
        "conversion_rate": 3.36,
        "revenue_per_recipient": 3.80
    },
    "segmentation": {
        "high_value_low_value_split": bool,
        "new_vs_returning_split": bool
    },
    "recommendations": [str]
}
```

---

### PAGE 11: Browse Abandonment Deep Dive
**Template**: `sections/flow_browse_abandonment.html`

#### Section Title
"BROWSE ABANDONMENT"

#### Workflow Diagram Data
```python
browse_abandonment_data = {
    "status": str,          # "missing" | "live" | "draft"
    "is_recommended": bool, # True (if missing)
    "workflow_steps": [
        {"type": "trigger", "name": "Viewed Product"},
        {"type": "filter", "name": "Has Not Started Checkout"},
        {"type": "delay", "duration": "4 hours"},
        {"type": "conditional", "branches": [
            {"condition": "0 prior emails", "email": "Email 1"},
            {"condition": "1 prior email", "email": "Email 2"},
            {"condition": "2+ prior emails", "email": "Email 3"}
        ]}
    ],
    "recommendations": [
        "Implement based on prior email interactions",
        "Use 'lighter touch points' than abandoned cart",
        "Avoid repetitive emails for frequent browsers"
    ]
}
```

---

### PAGE 12-13: Post Purchase & Strategies
**Template**: `sections/flow_post_purchase.html`

#### Section Title
"POST PURCHASE"

#### Retention Cohort Table Structure
```
┌────────┬──────┬───────┬───────┬───────┬───────┬───────┬───────┐
│Date    │Cohort│First  │Month 0│Month 1│Month 2│Month 3│Month 4│
│        │size  │order  │       │       │       │       │       │
├────────┼──────┼───────┼───────┼───────┼───────┼───────┼───────┤
│All     │3,504 │ 100%  │ 5.0%  │ 9.1%  │ 8.0%  │ 8.2%  │ 8.2%  │
│cohorts │      │       │       │       │       │       │       │
│Aug 2023│   3  │ 100%  │ 66.7% │ 66.7% │ 0.0%  │ 33.3% │ 0.0%  │
│Sep 2023│ 325  │ 100%  │ 5.2%  │ 9.8%  │ 11.4% │ 9.2%  │ 8.3%  │
└────────┴──────┴───────┴───────┴───────┴───────┴───────┴───────┘
```

#### Data Required
```python
post_purchase_data = {
    "retention_cohorts": [
        {
            "date": str,        # "All cohorts" | "Aug 2023"
            "cohort_size": int, # 3504
            "first_order": 100, # Always 100%
            "month_0": float,   # 5.0
            "month_1": float,   # 9.1
            "month_2": float,   # 8.0
            "month_3": float,   # 8.2
            "month_4": float,   # 8.2
            "month_5": float    # 0.0
        }
    ],
    "segmentation_strategy": {
        "first_time_customers": str,
        "returning_customers": str,
        "vip_customers": str
    },
    "strategies": [
        {
            "name": "Customised Thank You emails",
            "description": str
        },
        {
            "name": "Educational Content",
            "description": str
        },
        {
            "name": "Cross-Selling",
            "description": str
        },
        {
            "name": "Surprise and Delight",
            "description": str
        },
        {
            "name": "Purchase Anniversary & Milestone Flows",
            "description": str
        },
        {
            "name": "Lapsed Customer Flow",
            "description": str
        },
        {
            "name": "Dedicated Review Flows",
            "description": str
        }
    ]
}
```

---

### PAGE 14: Okendo Reviews Flows
**Template**: `sections/advanced_reviews.html`

#### Data Required
```python
reviews_data = {
    "integration": "Okendo",  # or "Yotpo", "Stamped", etc.
    "is_integrated": bool,
    "capabilities": [
        {
            "name": "Dynamic Flows",
            "description": "Trigger Klaviyo flows based on review events"
        },
        {
            "name": "Dynamic Content",
            "description": "Show product reviews in emails"
        },
        {
            "name": "Intelligent Automation",
            "description": "Set time delays based on delivery location"
        },
        {
            "name": "UGC Shoppables",
            "description": "Include photo/video reviews in galleries"
        }
    ],
    "recommendations": [str]
}
```

---

### PAGE 15-16: Wishlist Automation
**Template**: `sections/advanced_wishlist.html`

#### Section Title
"WISHLIST AUTOMATION"

#### Data Required
```python
wishlist_data = {
    "is_applicable": bool,      # Based on industry
    "integration": str,         # "Wishlist Plus" | "Swym" | etc.
    "triggers": [
        "Running low in stock",
        "Back in stock",
        "Price dropped or discounted"
    ],
    "tactics": [
        {
            "name": "Email Automations (Tactic 1)",
            "description": "Dedicated wishlist automation sequences",
            "flows": [
                "Wishlist nurture series",
                "Low-stock alert",
                "Price drop notification",
                "Back-in-stock notification"
            ]
        },
        {
            "name": "Email Automations (Tactic 2)",
            "description": "Content blocks in existing automations",
            "approach": "Show/hide wishlist CTA for non-account holders"
        }
    ],
    "visual_examples": [
        {"type": "sale_notification", "headline": "This Piece is On Sale!"},
        {"type": "wishlist_prompt", "headline": "Ready To Start a Wishlist?"}
    ]
}
```

---

### PAGE 17: Campaign Performance
**Template**: `sections/campaign_performance.html`

#### Section Title
"OVERALL CAMPAIGN PERFORMANCE"

#### Campaign Summary Table
```
┌───────────────┬────────────────┬──────────────┬─────────────┐
│ Average Open  │ Average Click  │ Average      │ Total       │
│ Rate          │ Rate           │ Placed Order │ Revenue     │
│               │                │ Rate         │             │
├───────────────┼────────────────┼──────────────┼─────────────┤
│    41.39%     │     4.73%      │    0.14%     │ $218,681.07 │
└───────────────┴────────────────┴──────────────┴─────────────┘
```

#### Benchmark Comparison Table
```
┌───────────┬────────────┬─────────────┬────────────────────┐
│ Open Rate │ Click Rate │ Conversion  │ Revenue Per        │
│           │            │ Rate        │ Recipient          │
├───────────┼────────────┼─────────────┼────────────────────┤
│  44.50%   │   1.66%    │   0.07%     │      $0.09         │
└───────────┴────────────┴─────────────┴────────────────────┘
(Industry Benchmark: Apparel and Accessories)
```

#### Data Required
```python
campaign_performance_data = {
    "summary": {
        "avg_open_rate": float,         # 41.39
        "avg_click_rate": float,        # 4.73
        "avg_placed_order_rate": float, # 0.14
        "total_revenue": float          # 218681.07
    },
    "benchmark": {
        "industry": str,                # "Apparel and Accessories"
        "open_rate": float,             # 44.50
        "click_rate": float,            # 1.66
        "conversion_rate": float,       # 0.07
        "revenue_per_recipient": float  # 0.09
    },
    "vs_benchmark": {
        "open_rate": str,       # "below" | "meets" | "exceeds"
        "click_rate": str,
        "conversion_rate": str
    },
    "analysis": {
        "campaigns_per_month": float,
        "primary_list": str,
        "segmentation_used": bool,
        "issues_identified": [str]
    },
    "recommendations": [str]
}
```

---

### PAGE 18: Segmentation Strategy
**Template**: `sections/segmentation_strategy.html`

#### Section Title
"Segmentation Strategy"

#### Engagement Tracks Table
```
┌─────────────────────────┬──────────────────────────────────────┐
│ Segment Name            │ Recommended Cadence                  │
├─────────────────────────┼──────────────────────────────────────┤
│ Track A: Highly Engaged │ Daily                                │
│ Track B: Moderately     │ 2-3x/week                            │
│          Engaged        │                                      │
│ Track C: Broad Engaged  │ 1x/week                              │
│ Track D: Unengaged      │ Goes through Sunset Flow then        │
│                         │ suppressed if remains unengaged      │
│ Track E: For Suppression│ Do not send. Needs to be suppressed  │
└─────────────────────────┴──────────────────────────────────────┘
```

#### Data Required
```python
segmentation_data = {
    "tracks": [
        {
            "name": "Track A: Highly Engaged",
            "cadence": "Daily",
            "criteria": "Opened/clicked in last 30 days"
        },
        {
            "name": "Track B: Moderately Engaged",
            "cadence": "2-3x/week",
            "criteria": "Opened/clicked in last 60 days"
        },
        {
            "name": "Track C: Broad Engaged",
            "cadence": "1x/week",
            "criteria": "Opened/clicked in last 90 days"
        },
        {
            "name": "Track D: Unengaged",
            "cadence": "Goes through Sunset Flow then suppressed",
            "criteria": "No engagement in 90+ days"
        },
        {
            "name": "Track E: For Suppression",
            "cadence": "Do not send. Needs to be suppressed",
            "criteria": "Hard bounces, complaints, unsubscribes"
        }
    ],
    "send_strategy": {
        "smart_send_time": bool,
        "description": str
    },
    "current_implementation": {
        "segments_exist": bool,
        "tracks_configured": int
    }
}
```

---

## 3. Data Requirements

### 3.1 Klaviyo API Data Points Needed

#### Revenue Data (Metric Aggregates)
```python
revenue_extraction = {
    "metric": "Placed Order",
    "measurements": ["count", "sum_value", "unique"],
    "time_periods": [
        {"name": "current_90_days", "days": 90},
        {"name": "previous_90_days", "days": 180, "offset": 90},
        {"name": "daily_breakdown", "interval": "day", "days": 90}
    ],
    "groupings": [
        "$attributed_flow",
        "$attributed_campaign",
        "$attributed_message"
    ]
}
```

#### List Growth Data
```python
list_growth_extraction = {
    "endpoints": [
        "/lists/{list_id}/profiles/",  # Current subscribers
        # Need to track over time via metric aggregates
    ],
    "metrics": [
        "Subscribed to List",
        "Unsubscribed from List"
    ],
    "time_series": {
        "interval": "month",
        "periods": 6
    }
}
```

#### Form Performance Data
```python
form_extraction = {
    "endpoint": "/forms/",
    "metrics_per_form": [
        "views",          # Impressions
        "submissions",    # Total submitted
        "submit_rate"     # Calculated
    ]
}
```

#### Flow Statistics
```python
flow_extraction = {
    "endpoint": "/flow-values-reports/",
    "statistics": [
        "recipients",
        "opens",
        "open_rate",
        "clicks", 
        "click_rate",
        "conversions",
        "conversion_rate",
        "revenue",
        "revenue_per_recipient"
    ],
    "core_flows": [
        "welcome",
        "abandoned_cart",
        "abandoned_checkout",
        "browse_abandonment",
        "post_purchase",
        "back_in_stock",
        "winback"
    ]
}
```

#### Campaign Statistics
```python
campaign_extraction = {
    "endpoint": "/campaign-values-reports/",
    "statistics": [
        "recipients",
        "opens",
        "open_rate", 
        "clicks",
        "click_rate",
        "conversions",
        "conversion_rate",
        "revenue"
    ]
}
```

### 3.2 Data Processing Requirements

```python
# Required calculations
calculations = {
    "kav_percentage": "klaviyo_revenue / total_revenue * 100",
    "flow_attribution": "flow_revenue / klaviyo_revenue * 100",
    "campaign_attribution": "campaign_revenue / klaviyo_revenue * 100",
    "submit_rate": "submissions / impressions * 100",
    "churn_rate": "lost_subscribers / new_subscribers * 100",
    "vs_previous_period": "(current - previous) / previous * 100"
}
```

---

## 4. Benchmark Specifications

### 4.1 Industry Benchmarks (Apparel & Accessories)

```json
{
    "industry": "Apparel & Accessories",
    "source": "Klaviyo Q4 2025 Benchmarks",
    
    "campaigns": {
        "open_rate": {"average": 44.50, "top_10": 55.00},
        "click_rate": {"average": 1.66, "top_10": 3.50},
        "conversion_rate": {"average": 0.07, "top_10": 0.25},
        "revenue_per_recipient": {"average": 0.09, "top_10": 0.35}
    },
    
    "flows": {
        "welcome_series": {
            "open_rate": {"average": 59.07, "top_10": 72.00},
            "click_rate": {"average": 5.70, "top_10": 12.00},
            "conversion_rate": {"average": 2.52, "top_10": 6.00},
            "revenue_per_recipient": {"average": 3.11, "top_10": 8.50}
        },
        "abandoned_cart": {
            "open_rate": {"average": 54.74, "top_10": 68.00},
            "click_rate": {"average": 6.25, "top_10": 14.00},
            "conversion_rate": {"average": 3.36, "top_10": 8.00},
            "revenue_per_recipient": {"average": 3.80, "top_10": 12.00}
        },
        "browse_abandonment": {
            "open_rate": {"average": 45.00, "top_10": 58.00},
            "click_rate": {"average": 4.50, "top_10": 9.00},
            "conversion_rate": {"average": 1.20, "top_10": 3.50},
            "revenue_per_recipient": {"average": 1.50, "top_10": 5.00}
        },
        "post_purchase": {
            "open_rate": {"average": 52.00, "top_10": 65.00},
            "click_rate": {"average": 3.80, "top_10": 8.00},
            "conversion_rate": {"average": 0.80, "top_10": 2.50},
            "revenue_per_recipient": {"average": 1.20, "top_10": 4.00}
        }
    },
    
    "list_health": {
        "growth_rate_monthly": {"average": 3.0, "top_10": 8.0},
        "churn_rate_monthly": {"average": 2.5, "top_10": 1.0},
        "engagement_rate": {"average": 25.0, "top_10": 45.0}
    },
    
    "forms": {
        "popup_submit_rate": {"average": 3.0, "top_10": 8.0},
        "embed_submit_rate": {"average": 0.5, "top_10": 2.0}
    },
    
    "kav": {
        "percentage": {"average": 25.0, "top_10": 40.0}
    }
}
```

### 4.2 Standing Classifications

```python
standing_rules = {
    "form_submit_rate": {
        "popup": {
            "Poor": "<1%",
            "Average": "1-3%",
            "Good": "3-8%",
            "Excellent": ">8%"
        },
        "embed": {
            "Poor": "<0.1%",
            "Average": "0.1-0.5%",
            "Good": "0.5-2%",
            "Excellent": ">2%"
        }
    },
    "flow_performance": {
        "significantly_below": "<50% of average",
        "below_average": "50-90% of average",
        "average": "90-110% of average",
        "above_average": "110-150% of average",
        "exceeds": ">150% of average"
    }
}
```

---

## 5. Visual Components

### 5.1 Chart Specifications

#### Revenue Trend Chart (KAV Analysis)
```javascript
chart_config = {
    type: "bar_line_combo",
    x_axis: "months",
    bars: [
        {name: "Attributed Revenue", color: "#4CAF50"},
        {name: "Unattributed Revenue", color: "#E0E0E0"}
    ],
    line: {
        name: "Total Recipients",
        color: "#333333",
        y_axis: "secondary"
    },
    height: 300,
    width: 500
}
```

#### List Growth Chart
```javascript
chart_config = {
    type: "bar",
    charts: [
        {
            title: "List size and growth",
            metric: "total_members",
            color: "#2196F3"
        },
        {
            title: "Net membership change", 
            metric: "net_change",
            color: "#4CAF50",  // Positive
            negative_color: "#F44336"  // Negative
        }
    ]
}
```

### 5.2 Table Styles

#### Data Table with Green Header
```css
.data-table-green {
    width: 100%;
    border-collapse: collapse;
}

.data-table-green thead {
    background: #65DA4F;  /* Andzen Green */
    color: #262626;
}

.data-table-green th {
    padding: 12px 16px;
    text-align: left;
    font-weight: 700;
}

.data-table-green td {
    padding: 12px 16px;
    border-bottom: 1px solid #E0E0E0;
}

.data-table-green tr:nth-child(even) {
    background: #F9FAFB;
}
```

### 5.3 Visual Mockup Components

#### Email Preview Cards
```html
<div class="email-preview-card">
    <div class="email-preview-image">
        <!-- Placeholder or actual screenshot -->
    </div>
    <div class="email-preview-caption">
        <h4>{{ headline }}</h4>
        <p>{{ description }}</p>
    </div>
</div>
```

---

## 6. Template Module Structure

### 6.1 Directory Structure

```
templates/
├── base.html                    # Base template with header/footer
├── audit_report.html           # Main orchestrator template
├── components/
│   ├── table_green_header.html # Reusable table component
│   ├── metric_card.html        # Metric display card
│   ├── benchmark_comparison.html # Benchmark vs actual table
│   ├── flow_card.html          # Flow summary card
│   ├── recommendation_card.html # Recommendation display
│   └── chart_placeholder.html  # Chart container
├── sections/
│   ├── cover.html              # Page 1
│   ├── kav_analysis.html       # Page 2-3
│   ├── list_growth.html        # Page 4
│   ├── data_capture.html       # Page 5-6
│   ├── automation_overview.html # Page 7
│   ├── flow_welcome.html       # Page 8
│   ├── flow_abandoned_cart.html # Page 9-10
│   ├── flow_browse_abandonment.html # Page 11
│   ├── flow_post_purchase.html # Page 12-13
│   ├── advanced_reviews.html   # Page 14
│   ├── advanced_wishlist.html  # Page 15-16
│   ├── campaign_performance.html # Page 17
│   └── segmentation_strategy.html # Page 18
└── assets/
    ├── styles.css              # Main stylesheet
    ├── print.css               # Print-specific styles
    ├── charts.js               # Chart rendering
    └── images/
        ├── andzen_logo.svg
        ├── brush_stroke.svg
        └── icons/
```

### 6.2 Template Inheritance

```html
<!-- base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="assets/styles.css">
    <link rel="stylesheet" href="assets/print.css" media="print">
</head>
<body>
    {% block content %}{% endblock %}
    <script src="assets/charts.js"></script>
</body>
</html>
```

```html
<!-- audit_report.html -->
{% extends "base.html" %}

{% block content %}
<div class="audit-report">
    {% include "sections/cover.html" %}
    
    <div class="page-break"></div>
    {% include "sections/kav_analysis.html" %}
    
    <div class="page-break"></div>
    {% include "sections/list_growth.html" %}
    
    <!-- ... more sections ... -->
</div>
{% endblock %}
```

### 6.3 Component Usage

```html
<!-- Using table component -->
{% include "components/table_green_header.html" with 
    headers=["Flow Name", "Open Rate", "Click Rate", "Revenue"]
    rows=automation_data.flows
%}

<!-- Using metric card -->
{% include "components/metric_card.html" with
    label="Total Revenue"
    value=kav_data.revenue.total_website_formatted
    subtext="↗ " + kav_data.revenue.vs_previous_period|string + "% vs previous"
%}
```

---

## 7. CSS Styling Guide

### 7.1 Brand Colors (Andzen)

```css
:root {
    /* Primary */
    --andzen-black: #000000;
    --andzen-charcoal: #262626;
    --andzen-green: #65DA4F;
    --andzen-white: #FFFFFF;
    
    /* Accent */
    --andzen-grey: #B7B9BC;
    --andzen-orange: #EB9E1D;
    
    /* Status */
    --status-excellent: #10B981;
    --status-good: #65DA4F;
    --status-average: #F59E0B;
    --status-poor: #EF4444;
}
```

### 7.2 Typography

```css
/* Headers - Bebas Neue */
h1, h2 {
    font-family: 'Bebas Neue', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Body - Montserrat */
body, p, td {
    font-family: 'Montserrat', sans-serif;
    font-weight: 400;
}

/* Data/Code - Space Mono */
.metric-value, code, .mono {
    font-family: 'Space Mono', monospace;
}
```

### 7.3 Print Optimization

```css
@media print {
    .page-break {
        page-break-after: always;
    }
    
    .no-break {
        page-break-inside: avoid;
    }
    
    .section {
        page-break-inside: avoid;
        margin: 0;
        padding: 20mm;
    }
    
    @page {
        size: A4;
        margin: 15mm;
    }
}
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Create `data/benchmarks/comprehensive_benchmarks.json`
- [ ] Create template directory structure
- [ ] Create base template and components
- [ ] Update CSS with all required styles

### Phase 2: Data Extraction
- [ ] Add list growth extraction to `klaviyo.py`
- [ ] Add form performance extraction
- [ ] Add 90-day time series extraction
- [ ] Add retention cohort calculation

### Phase 3: Section Templates
- [ ] `cover.html`
- [ ] `kav_analysis.html`
- [ ] `list_growth.html`
- [ ] `data_capture.html`
- [ ] `automation_overview.html`
- [ ] `flow_welcome.html`
- [ ] `flow_abandoned_cart.html`
- [ ] `flow_browse_abandonment.html`
- [ ] `flow_post_purchase.html`
- [ ] `advanced_reviews.html`
- [ ] `advanced_wishlist.html`
- [ ] `campaign_performance.html`
- [ ] `segmentation_strategy.html`

### Phase 4: Analysis Enhancement
- [ ] Update `analysis.py` agents for deeper insights
- [ ] Add benchmark comparison logic
- [ ] Add narrative generation for each section

### Phase 5: Integration & Testing
- [ ] Update `report.py` to use new templates
- [ ] Implement PDF export
- [ ] Test against Morrison sample
- [ ] Quality verification

---

*Document Version: 1.0*
*Last Updated: December 17, 2025*

