# Klaviyo Prospect Audit Automation

Automated audit report generation for Klaviyo prospects using FastAPI, Claude AI, and Klaviyo API.

## Project Structure

```
prospect-audit-automation/
├── api/
│   ├── main.py              # FastAPI app
│   ├── routes/
│   │   └── audit.py         # Audit endpoints
│   ├── services/
│   │   ├── klaviyo.py       # Klaviyo API client
│   │   ├── benchmark.py     # Benchmark comparison
│   │   ├── analysis.py      # AI analysis (Claude)
│   │   └── report.py        # Report generation
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── utils/
│       └── helpers.py       # Utility functions
├── templates/
│   ├── audit_template.html  # Main template
│   ├── sections/            # Section templates
│   │   ├── cover.html
│   │   ├── executive_summary.html
│   │   └── ...
│   └── assets/
│       ├── andzen_logo.png
│       └── styles.css
├── data/
│   ├── benchmarks/
│   │   └── fashion_accessories.json
│   └── cache/               # Cached API responses
├── scripts/
│   └── test_klaviyo.py      # Test script
├── tests/
├── .env                     # Environment variables
├── requirements.txt
└── README.md
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file with:
   ```
   KLAVIYO_API_KEY=your_klaviyo_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

3. **Test Klaviyo connection:**
   ```bash
   python scripts/test_klaviyo.py
   ```

4. **Run the API server:**
   ```bash
   uvicorn api.main:app --reload
   ```

## API Endpoints

### Generate Audit Report
```
POST /api/audit/generate
```

Request body:
```json
{
  "api_key": "your_klaviyo_api_key",
  "client_name": "Client Name",
  "date_range": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-12-31T23:59:59"
  },
  "auditor_name": "Auditor Name"
}
```

### Test Connection
```
GET /api/audit/test-connection?api_key=your_api_key
```

## Features

- **Automated Data Extraction**: Pulls data from Klaviyo API
- **AI-Powered Analysis**: Uses Claude AI for insights and recommendations
- **Benchmark Comparison**: Compares metrics against industry benchmarks
- **Report Generation**: Creates professional HTML audit reports
- **Modular Architecture**: Easy to extend and customize

## Development

### Running Tests
```bash
pytest tests/
```

### Adding New Sections
1. Create a new template in `templates/sections/`
2. Update `api/services/report.py` to include the section
3. Add data extraction logic in `api/services/klaviyo.py` if needed

## License

Proprietary - Andzen

