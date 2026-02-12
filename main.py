import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# =========================
# Read Environment Variables
# (Render uses dashboard env vars)
# =========================
RMS_API_KEY = os.getenv("RMS_API_KEY")
RMS_HOST = os.getenv("RMS_HOST")

if not RMS_API_KEY or not RMS_HOST:
    raise RuntimeError("Missing RMS_API_KEY or RMS_HOST")

# =========================
# FastAPI app
# =========================
app = FastAPI(title="RMS Composite Lookup")

# =========================
# Request schema
# =========================
class LookupRequest(BaseModel):
    address: str


# =========================
# Address Parser
# =========================
def parse_address(address_str: str):
    """
    Expected format:
    425 Martin Lane, Beverly Hills, CA 90210
    """
    try:
        parts = [p.strip() for p in address_str.split(",")]
        street = parts[0]
        city = parts[1]
        state_zip = parts[2].split()
        state = state_zip[0]
        zip_code = state_zip[1]
        return street, city, state, zip_code
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Address format must be: Street, City, State ZIP"
        )


# =========================
# Simple Frontend Page
# =========================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>RMS Composite Lookup</title>
  <style>
    body {
        font-family: Arial, sans-serif;
        max-width: 900px;
        margin: 60px auto;
        padding: 0 16px;
    }
    h1 { margin-bottom: 10px; }
    .hint { color: #555; margin-bottom: 20px; }
    .row { display: flex; gap: 10px; }
    input {
        flex: 1;
        padding: 12px;
        font-size: 16px;
    }
    button {
        padding: 12px 18px;
        font-size: 16px;
        cursor: pointer;
    }
    pre {
        background: #f6f8fa;
        padding: 16px;
        border-radius: 8px;
        overflow: auto;
        margin-top: 20px;
    }
  </style>
</head>
<body>
  <h1>RMS Composite Lookup</h1>
  <div class="hint">
    Format: Street, City, State ZIP<br>
    Example: 425 Martin Lane, Beverly Hills, CA 90210
  </div>

  <div class="row">
    <input id="address" placeholder="Enter address here..." />
    <button onclick="lookup()">Search</button>
  </div>

  <pre id="output">Result will appear here...</pre>

  <script>
    async function lookup() {
      const address = document.getElementById('address').value.trim();
      const output = document.getElementById('output');

      if (!address) {
        output.textContent = "Please enter an address.";
        return;
      }

      output.textContent = "Loading...";

      try {
        const response = await fetch('/lookup', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ address })
        });

        const text = await response.text();

        if (!response.ok) {
          output.textContent = "Error " + response.status + "\\n" + text;
          return;
        }

        output.textContent = JSON.stringify(JSON.parse(text), null, 2);
      } catch (err) {
        output.textContent = "Request failed: " + err;
      }
    }
  </script>
</body>
</html>
"""


# =========================
# API Endpoint
# =========================
@app.post("/lookup")
def lookup(req: LookupRequest):

    street, city, state, zip_code = parse_address(req.address)

    url = f"{RMS_HOST}/li/composite"

    headers = {
        "content-type": "application/json",
        "authorization": RMS_API_KEY
    }

    payload = {
        "location": {
            "address": {
                "streetAddress": street,
                "cityName": city,
                "admin1Code": state,
                "postalCode": zip_code,
                "countryCode": "US",
                "countryRmsCode": "US",
                "countryScheme": "ISO2A",
                "rmsGeoModelResolutionCode": "2"
            },
            "coverageValues": {
                "buildingValue": 2950000,
                "contentsValue": 100000
            }
        },
        "layers": [
            {"name": "geocode", "version": "latest"},
            {"name": "us_wf_risk_score", "version": "2.0"},
            {"name": "us_wf_loss_cost", "version": "latest"}
        ]
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    return response.json()