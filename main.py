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
<title>RMS Wildfire Risk Lookup</title>

<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial;
    background-color: #f4f6f9;
    margin: 0;
    padding: 40px;
}

.container {
    max-width: 1000px;
    margin: auto;
}

h1 {
    margin-bottom: 5px;
}

.subtitle {
    color: #666;
    margin-bottom: 30px;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    margin-bottom: 20px;
}

.input-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
}

input {
    padding: 10px;
    font-size: 14px;
    border: 1px solid #ddd;
    border-radius: 6px;
}

button {
    padding: 12px;
    font-size: 15px;
    background-color: #1f4ed8;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    margin-top: 10px;
}

button:hover {
    background-color: #1e40af;
}

.section-title {
    font-weight: 600;
    margin-bottom: 10px;
    border-bottom: 1px solid #eee;
    padding-bottom: 5px;
}

.metric {
    margin: 5px 0;
}

.loading {
    color: #666;
    font-style: italic;
}
</style>
</head>

<body>

<div class="container">

<h1>RMS Wildfire Risk Lookup</h1>
<div class="subtitle">Internal underwriting tool</div>

<div class="card">
    <div class="section-title">Property Information</div>

    <div class="input-grid">
        <input id="address" placeholder="Street, City, State ZIP" />
        <input id="year_built" type="number" placeholder="Year Built" />
        <input id="num_stories" type="number" placeholder="Number of Stories" />
        <input id="sqft" type="number" placeholder="Square Footage" />
        <input id="building_value" type="number" placeholder="Building Value" />
        <input id="contents_value" type="number" placeholder="Contents Value" />
    </div>

    <button onclick="lookup()">Run Risk Analysis</button>
</div>

<div id="results"></div>

</div>

<script>
async function lookup() {

    const address = document.getElementById("address").value.trim();
    const resultsDiv = document.getElementById("results");

    if (!address) {
        resultsDiv.innerHTML = "<div class='card'>Address is required.</div>";
        return;
    }

    resultsDiv.innerHTML = "<div class='card loading'>Running analysis...</div>";

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

        const data = await response.json();

        if (!response.ok) {
            resultsDiv.innerHTML = "<div class='card'>Error: " + JSON.stringify(data) + "</div>";
            return;
        }

        function formatDecimal(value, digits=4) {
            if (value === null || value === undefined) return "-";
            return Number(value).toFixed(digits);
        }

        function formatPercent(value, digits=4) {
            if (value === null || value === undefined) return "-";
            return (Number(value) * 100).toFixed(digits) + "%";
        }

        function formatCurrency(value) {
            if (value === null || value === undefined) return "-";
            return new Intl.NumberFormat("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(Number(value));
        }

        resultsDiv.innerHTML = `
        <div class="card">
            <div class="section-title">Location</div>
            <div class="metric">Address: ${data.location.address}</div>
            <div class="metric">City: ${data.location.city}</div>
            <div class="metric">County: ${data.location.county}</div>
            <div class="metric">State: ${data.location.state}</div>
            <div class="metric">ZIP: ${data.location.postal_code}</div>
            <div class="metric">Latitude: ${formatDecimal(data.location.latitude)}</div>
            <div class="metric">Longitude: ${formatDecimal(data.location.longitude)}</div>
        </div>

        <div class="card">
            <div class="section-title">Wildfire Risk</div>
            <div class="metric">Overall Score: ${data.wildfire_risk.overall_score}</div>
            <div class="metric">100 Year: ${data.wildfire_risk.score_100yr}</div>
            <div class="metric">250 Year: ${data.wildfire_risk.score_250yr}</div>
            <div class="metric">500 Year: ${data.wildfire_risk.score_500yr}</div>
        </div>

        <div class="card">
            <div class="section-title">Loss Metrics</div>
            <div class="metric">Building ALR: ${formatPercent(data.loss_metrics.building_annual_loss_rate)}</div>
            <div class="metric">Contents ALR: ${formatPercent(data.loss_metrics.contents_annual_loss_rate)}</div>
            <div class="metric">Ground Up Loss: ${formatCurrency(data.loss_metrics.ground_up_loss)}</div>
        </div>
        `;

    } catch (err) {
        resultsDiv.innerHTML = "<div class='card'>Request failed: " + err + "</div>";
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

    data = response.json()

    geocode = next((x for x in data if x["name"] == "geocode"), {})
    risk = next((x for x in data if x["name"] == "us_wf_risk_score"), {})
    loss = next((x for x in data if x["name"] == "us_wf_loss_cost"), {})

    geo_res = geocode.get("results", {})
    risk_res = risk.get("results", {})
    loss_res = loss.get("results", {})

    result = {
        "location": {
            "address": geo_res.get("streetAddress"),
            "city": geo_res.get("cityName"),
            "county": geo_res.get("admin2Name"),
            "state": geo_res.get("admin1Code"),
            "postal_code": geo_res.get("postalCode"),
            "latitude": geo_res.get("latitude"),
            "longitude": geo_res.get("longitude")
        },
        "wildfire_risk": {
            "overall_score": risk_res.get("scoreOverall"),
            "score_100yr": risk_res.get("score100yr"),
            "score_250yr": risk_res.get("score250yr"),
            "score_500yr": risk_res.get("score500yr")
        },
        "loss_metrics": {
            "building_annual_loss_rate": loss_res.get("buildingAlr"),
            "contents_annual_loss_rate": loss_res.get("contentsAlr"),
            "ground_up_loss": loss_res.get("groundUpLoss")
        }
    }

    return result
