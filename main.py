from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/get_fargo_parcel")
def get_fargo_parcel(query: str):
    if "-" in query:
        url = "https://gis.cityoffargo.com/arcgis/rest/services/Basemap/FargoParcels/FeatureServer/0/query"
        params = {
            "where": f"ParcelNo = '{query}'",
            "outFields": "*",
            "f": "json"
        }
    else:
        url = "https://gis.cityoffargo.com/arcgis/rest/services/Basemap/FargoParcels/FeatureServer/0/query"
        params = {
            "where": f"LandAddr = '{query.upper()}'",
            "outFields": "*",
            "f": "json"
        }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if "features" not in data or not data["features"]:
        return {"error": "No parcel found for this input."}

    return data["features"][0]["attributes"]
