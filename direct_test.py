import json
import requests

# api-use1.rms ~ use for U.S. based
API_URL = 'https://api-use1.rms.com/li/composite'

# OnwardAPITesting
# I forgot but remember that these calls get updated at midnight so you won't see your activity until next day  
YOUR_API_KEY = 'fVE9FEEY8EiIp5N8pTdFxE8K1OXj68siyQaTyffTNpk'

# nothing fancy here
headers = {
    'content-type': 'application/json',
    'authorization': YOUR_API_KEY
}

# from documentation, I saw they would define the url as
# url = https://api-use1.rms.com + {}
# where {} in this case would be /li/composite
# recall they mentioned we would want to use composite in our calls 
url = API_URL

# pure JSON syntax
# we should keep track of all of these somewhere
# admin1Code = State
# countryScheme = ? no clue hahaha lets try to figure out what this is
request = {
    "location": {
        "address":{
            "admin1Code": "CA",
            "cityName": "NEWARK",
            "countryCode": "US",
            "countryScheme": "ISO2A",
            "postalCode": "94560",
            "streetAddress": "7575 GATEWAY BLVD"
        },
        # ATC1 ~ this is likely going to be in the Support Center "TBC" 
        # TO BE CONFIRMED
        "characteristics": {
            "construction" : "ATC1",
            "occupancy" : "ATC1",
            "yearBuilt" : 1973,
            "numOfStories": 3,
            "foundationType": 0,
            "basement": "DEFAULT",
            "floorArea": 0
        },
        "coverageValues" : {
            "buildingValue": 1000000,
            "contentsValue": 100000,
            "businessInterruptionValue": 5000
        }
    },
    "layers" : [
        {
            "name" : "geocode",
            "version" : "latest"
        },
        {
            "name" : "us_wf_risk_score",
            "version" : "2.0"
        }
    ]
}

response = requests.post(url, json=request, headers=headers)

print("Status Code:", response.status_code)
print("Response text:")
print(response.text)

try:
    response_json = response.json()
    print("Parsed JSON:")
    print(response_json)
except Exception as e:
    print("JSON parse error:", e)
