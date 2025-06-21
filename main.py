from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Format "LASTNAME, FIRSTNAME" to "Firstname Lastname"
def format_owner_name(owner_raw):
    if not owner_raw:
        return ""
    owners = owner_raw.split("&")
    formatted_owners = []
    for owner in owners:
        parts = owner.strip().split(",")
        if len(parts) == 2:
            formatted_owners.append(f"{parts[1].strip().title()} {parts[0].strip().title()}")
        else:
            formatted_owners.append(owner.strip().title())
    return " & ".join(formatted_owners)

# Define only the required fields
REQUIRED_FIELDS = ["OwnerName", "PropertyAddress"]

@app.get("/get_fargo_parcel")
def get_fargo_parcel(query: str):
    base_url = "https://gis.cityoffargo.com/arcgis/rest/services/Basemap/FargoParcels/FeatureServer/0/query"
    
    where_clause = f"ParcelNo = '{query}'" if "-" in query else f"LandAddr = '{query.upper()}'"
    params = {
        "where": where_clause,
        "outFields": "*",
        "f": "json"
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()

    if "features" not in data or not data["features"]:
        raise HTTPException(status_code=404, detail="No parcel found for this input.")

    attr = data["features"][0]["attributes"]

    # Log raw response for debugging
    print("🔍 Raw Parcel Data:", attr)

    # Field mapping
    mapped = {
        "OwnerName": format_owner_name(attr.get("Owner1")),
        "PropertyAddress": f"{attr.get('LandAddr', '').strip().title()}, Fargo, ND {attr.get('LandZip')}",
        "PropertyZip": attr.get("LandZip"),
        "MailingAddress": attr.get("MailAddr"),
        "MailingCity": attr.get("MailCity"),
        "MailingState": attr.get("MailSt"),
        "Acreage": round(attr.get("ACRES", 0), 2),
        "LotSize": f"{int(attr.get('SegSqFt', 0))} sq ft",
        "Zoning": attr.get("Zone1"),
        "LegalDescription": f"Lots {attr.get('LotLegal')}, Block {attr.get('BlockLegal')}, {attr.get('AdditionName')}",
        "PropertyValue": f"${int(attr.get('TotalValue', 0)):,}",
        "LandValue": f"${int(attr.get('LandValue', 0)):,}",
        "BuildingValue": f"${int(attr.get('BldgValue', 0)):,}",
        "YearBuilt": attr.get("YrBuilt"),
        "BuildingSF": f"{attr.get('BldgSF')} sq ft" if attr.get("BldgSF") else None,
        "PropertyType": attr.get("TypeDesc"),
        "UseType": attr.get("UseCodeDesc"),
        "ElementarySchool": attr.get("ElemSch"),
        "JuniorHighSchool": attr.get("JrHighSchool"),
        "HighSchool": attr.get("HighSchool"),
        "Neighborhood": attr.get("NeighborhoodArea"),
        "Block": attr.get("BlockLegal"),
        "Lot": attr.get("LotLegal"),
        "Addition": attr.get("AdditionName")
    }

    # Check for required fields
    missing_fields = [key for key in REQUIRED_FIELDS if not mapped.get(key)]

    # Log mapped result and validation
    print("✅ Mapped Merge Fields:", mapped)
    if missing_fields:
        print("⚠️ Missing Required Fields:", missing_fields)

    return {
        "merge_fields": mapped,
        "missing_required_fields": missing_fields
    }

