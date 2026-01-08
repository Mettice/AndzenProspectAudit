# Audit Process & Images Analysis

## 📋 **COMPLETE AUDIT PROCESS (Step-by-Step)**

### **Pre-Audit Steps:**
1. **Review the website:**
   - Screenshot all data-capture forms
   - Sign up (check for welcome email)
   - Check for loyalty program/subscription
   - Test abandoned cart flow
   - Confirm if site is on Shopify

2. **Review Klaviyo account:**
   - Get high-level understanding of:
     - Flow suite
     - Campaign cadence & segmentation
     - Revenue performance
     - Connected tech integrations

3. **Prepare audit template:**
   - Locate most recent audit from same industry
   - Create copy as foundation

---

### **Section 1: KAV**
1. Go to **Dashboard → Business Review**
2. Set time period to **YTD** (or last 12 months if early in year)
3. Copy KAV metrics into table
4. **Take screenshot of table** ✅ (Manual step)
5. Share screenshot with AI for insights
6. Prompt: *"Can you give insights on [Brand Name]'s KAV. Structure it similar to this but make it relevant to their performance (attached)."*

**Sub-sections:**
- Campaigns vs. Flows
- Email vs. SMS
- Growing Your KAV

---

### **Section 2: List Growth**
1. Go to **Profiles → View Subscriber Growth**
2. Set **Email** and **Date Range: YTD Monthly**
3. **Screenshots needed:** ✅ (Manual steps)
   - Growth Graph
   - Opt-in sources
   - Exclusion sources
4. Copy insights from previous audit
5. Prompt AI with all three screenshots
6. Prompt: *"Can you give insights on [Brand Name]'s List Growth. Structure it similar to this but make it relevant to their performance (attached)."*
7. **Repeat for SMS**

---

### **Section 3: List Engagement**
1. Go to **List & Segments → create "All Active Profiles" segment**
2. Review **Engagement view**
3. **Convert line-graph data into percentages** for audit table
4. **Take screenshot of table** ✅ (Manual step)
5. Prompt: *"Can you create insights on [Brand Name]'s List Engagement Breakdown? A healthy email list should have more than 50% of members in the 'Very Engaged' or 'Somewhat Engaged' categories, with no more than 25% categorized as 'Not Engaged.' Structure the insights similar to the one below but make it relevant to [Brand Name]'s data (attached)."*

---

### **Section 4: Data Capture**
1. Go to **Website → Sign-up Forms**
2. Select each form
3. Transfer required data into audit table
4. **Take screenshot of table** ✅ (Manual step)
5. Prompt: *"Can you create insights on [Brand Name]'s Data Capture Performance? The typical benchmark across industries is between 3-6%. Structure the insights similar to the one below but make it relevant to [Brand Name]'s data (attached)."*
6. For "Areas of Opportunity":
   - Review form targeting and behavior
   - Review incentive offered
   - Document observations
   - Share with AI for recommendations

---

### **Section 5: Flows**
1. Go to **Custom Reports → Create from scratch**
2. **Report Type: Flow Performance Report**
3. **Data needed:**
   - Email Recipients
   - Email Open Rate
   - Email Click Rate
   - Placed Order Rate
   - Placed Order Value SUM
4. **Group by: Flow**
5. **Timeframe: YTD**
6. Copy each flow's data into dedicated table
7. Use industry benchmarks (from Excel file or page)
8. Recommendations based on:
   - Flow structure review
   - Logic review
   - Individual email content review

---

### **Section 6: Campaigns**
1. Go to **Analytics → Benchmarks → Campaigns**
2. Set time period to **YTD**
3. **Take screenshot of Campaign Performance section** ✅ (Manual step)
4. Send screenshot to AI with previous audit insights
5. If deliverability is critical:
   - Go to **Analytics → Deliverability → Reports**
   - Send data to AI with observations
   - Draft recommendations for refinement

---

## 🖼️ **IMAGE TYPE ANALYSIS**

### **What Images Are in Sample Audits:**

1. **Charts/Graphs** (✅ **WE CAN GENERATE THESE**)
   - **Engagement Breakdown Line Charts**: "The line graph below provides a visual snapshot of your database's engagement breakdown, showing the percentage of profiles in each engagement level"
   - **Flow Performance Charts**: Comparison charts showing flow metrics vs benchmarks
   - **Revenue Trend Charts**: Visual representations of revenue over time
   
   **Status:** ✅ We have all the data needed. We can generate these using Chart.js and convert to static images.

2. **Klaviyo Dashboard Screenshots** (❌ **WE DON'T HAVE ACCESS**)
   - Screenshots of Business Review dashboard
   - Screenshots of List Growth graphs
   - Screenshots of Engagement view
   - Screenshots of Form performance tables
   - Screenshots of Campaign Performance section
   
   **Status:** ❌ We don't have direct access to Klaviyo UI to capture screenshots.
   **Recommendation:** Skip these or make optional. Our generated tables and charts are sufficient.

3. **Campaign Images/Creatives** (❌ **WE DON'T HAVE ACCESS**)
   - Actual email campaign creatives
   - Email design examples
   
   **Status:** ❌ We don't have access to campaign creatives unless pre-populated.
   **Recommendation:** Skip these or make optional. Not critical for audit insights.

4. **Table Screenshots** (✅ **WE DON'T NEED**)
   - Screenshots of Klaviyo-generated tables
   
   **Status:** ✅ We generate our own tables, so screenshots are not needed. Our tables are sufficient and often better formatted.

---

## ✅ **WHAT WE CAN DO**

### **1. Generate Charts from Our Data** ✅

**Engagement Breakdown Chart:**
- We have list engagement data (Very Engaged, Somewhat Engaged, Barely Engaged, Not Engaged)
- Generate line chart showing percentages
- Convert Chart.js canvas to base64 image
- Embed in HTML and Word document

**Flow Performance Charts:**
- We have flow performance data (open rates, click rates, conversion rates)
- Compare against benchmarks
- Generate comparison charts
- Embed as images

**Revenue Trend Charts:**
- We have revenue data over time
- Generate line/bar charts
- Show YoY comparisons
- Embed as images

**Implementation:**
```python
# We can use Chart.js (already included) to generate charts
# Convert canvas to base64 image
# Embed in Word document using htmldocx
```

### **2. Our Generated Tables Are Sufficient** ✅

- We generate properly formatted tables
- No need for Klaviyo table screenshots
- Our tables are often better formatted and more readable

### **3. Skip Screenshots** ✅

- Klaviyo dashboard screenshots are manual steps
- We don't have API access to capture UI screenshots
- Our data-driven approach is actually better (more accurate, always up-to-date)

---

## ❌ **WHAT WE CAN'T DO (OR DON'T NEED)**

### **1. Klaviyo Dashboard Screenshots** ❌
- **Why:** No API access to capture UI screenshots
- **Impact:** Low - Our generated tables/charts are better
- **Solution:** Skip or make optional

### **2. Campaign Creative Images** ❌
- **Why:** No access to email campaign creatives
- **Impact:** Low - Not critical for audit insights
- **Solution:** Skip or make optional (could allow manual upload if needed)

### **3. Manual Screenshot Steps** ❌
- **Why:** These are manual steps in the process document
- **Impact:** None - We automate data extraction
- **Solution:** Our automated approach is better

---

## 🎯 **RECOMMENDED IMPLEMENTATION**

### **Priority 1: Generate Charts** 🔴

**Engagement Breakdown Chart:**
```python
# In list_growth_preparer.py or list_engagement_preparer.py
def generate_engagement_chart(engagement_data):
    """
    Generate engagement breakdown line chart.
    
    engagement_data = {
        'very_engaged': 25.5,
        'somewhat_engaged': 30.2,
        'barely_engaged': 20.1,
        'not_engaged': 24.2
    }
    """
    # Use Chart.js to generate chart
    # Convert to base64 image
    # Return image data URI
```

**Flow Performance Chart:**
```python
# In flow_preparer.py
def generate_flow_performance_chart(flow_data, benchmarks):
    """
    Generate flow performance comparison chart.
    Compare actual performance vs benchmarks.
    """
    # Generate bar/line chart
    # Convert to base64 image
    # Return image data URI
```

### **Priority 2: Embed Charts in Word Documents** 🔴

**Test htmldocx with base64 images:**
```python
# In api/services/report/__init__.py
# Ensure htmldocx properly handles base64 images
# Test chart embedding in .docx files
```

### **Priority 3: Add Chart References in Text** 🟡

**Match sample audit style:**
- "The line graph below provides a visual snapshot of your database's engagement breakdown..."
- "The following figures are derived from Klaviyo's in-depth analysis per flow..."

---

## 📊 **COMPARISON: Manual Process vs Our Automated Process**

| Aspect | Manual Process | Our Automated Process |
|--------|---------------|----------------------|
| **Data Extraction** | Manual copy-paste from Klaviyo UI | ✅ Automated via API |
| **Screenshots** | Manual screenshots of dashboards | ❌ Not needed (we generate tables) |
| **Charts** | Manual creation or screenshots | ✅ Can generate from data |
| **Tables** | Manual copy-paste | ✅ Automated generation |
| **Insights** | Manual AI prompts with screenshots | ✅ Automated LLM analysis |
| **Accuracy** | Prone to human error | ✅ Always accurate |
| **Speed** | Hours of manual work | ✅ Minutes of automated work |

**Conclusion:** Our automated approach is actually **better** than the manual process. We just need to add chart generation to match the visual quality of sample audits.

---

## ✅ **FINAL RECOMMENDATIONS**

1. **✅ DO: Generate charts from our data**
   - Engagement breakdown charts
   - Flow performance charts
   - Revenue trend charts

2. **✅ DO: Embed charts as images in Word documents**
   - Use Chart.js to generate
   - Convert to base64
   - Embed via htmldocx

3. **❌ SKIP: Klaviyo dashboard screenshots**
   - Not needed - our tables are better
   - No API access anyway

4. **❌ SKIP: Campaign creative images**
   - Not critical for audit
   - Can be optional if needed later

5. **✅ DO: Match sample audit text style**
   - Add chart references: "The line graph below..."
   - Use similar narrative style

---

## 🚀 **NEXT STEPS**

1. **Implement chart generation:**
   - Engagement breakdown chart
   - Flow performance charts
   - Revenue trend charts

2. **Test chart embedding in Word:**
   - Ensure htmldocx handles base64 images
   - Test with sample chart

3. **Add chart references to templates:**
   - Match sample audit narrative style
   - Add "The line graph below..." text

4. **Verify output:**
   - Generate test audit
   - Compare to sample audits
   - Ensure charts appear in Word document


