import os
import requests
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# =========================
# Environment Variables
# =========================
RMS_API_KEY = os.getenv("RMS_API_KEY")
RMS_HOST = os.getenv("RMS_HOST")

if not RMS_API_KEY or not RMS_HOST:
    raise RuntimeError("Missing RMS_API_KEY or RMS_HOST")

# =========================
# FastAPI App
# =========================
app = FastAPI(title="RMS Composite Lookup")


# =========================
# Request Model
# =========================
class LookupRequest(BaseModel):
    address: str
    year_built: Optional[int] = 0
    num_stories: Optional[int] = 0
    sqft: Optional[int] = 0
    building_value: Optional[float] = 0
    contents_value: Optional[float] = 0


# =========================
# Address Parser
# =========================
def parse_address(address_str: str):
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
# Frontend UI
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
body { font-family: Arial; max-width: 900px; margin: 50px auto; }
h1 { margin-bottom: 10px; }
.row { display: flex; gap: 10px; margin-bottom: 10px; }
input { flex: 1; padding: 10px; font-size: 14px; }
button { padding: 10px; font-size: 14px; cursor: pointer; }
pre { background: #f6f8fa; padding: 15px; border-radius: 6px; overflow:auto; }
</style>
</head>
<body>

<h1>RMS Composite Lookup</h1>

<div class="row">
  <input id="address" placeholder="Street, City, State ZIP" />
</div>

<div class="row">
  <input id="year_built" type="number" placeholder="Year Built" />
  <input id="num_stories" type="number" placeholder="Number of Stories" />
</div>

<div class="row">
  <input id="sqft" type="number" placeholder="Square Footage" />
</div>

<div class="row">
  <input id="building_value" type="number" placeholder="Building Value" />
  <input id="contents_value" type="number" placeholder="Contents Value" />
</div>

<div class="row">
  <button onclick="lookup()">Search</button>
</div>

<pre id="output">Result will appear here...</pre>

<script>
async function lookup() {

  const address = document.getElementById("address").value.trim();
  const output = document.getElementById("output");

  if (!address) {
    output.textContent = "Address is required.";
    return;
  }

  output.textContent = "Loading...";

  try {
    const response = await fetch("/lookup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        address: address,
        year_built: parseInt(document.getElementById("year_built").value) || 0,
        num_stories: parseInt(document.getElementById("num_stories").value) || 0,
        sqft: parseInt(document.getElementById("sqft").value) || 0,
        building_value: parseFloat(document.getElementById("building_value").value) || 0,
        contents_value: parseFloat(document.getElementById("contents_value").value) || 0
      })
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
            "characteristics": {
                "construction": "ATC1",
                "occupancy": "ATC1",
                "yearBuilt": req.year_built or 0,
                "numOfStories": req.num_stories or 0,
                "foundationType": 0,
                "floorArea": req.sqft or 0
            },
            "coverageValues": {
                "buildingValue": req.building_value or 0,
                "contentsValue": req.contents_value or 0
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