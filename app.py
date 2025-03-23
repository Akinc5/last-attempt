import pdfplumber
import pandas as pd
import folium
from folium.features import DivIcon
import requests
import time
import os
from flask import Flask, render_template, jsonify, send_from_directory
from flask import request

app = Flask(__name__)

# Directory for static files
os.makedirs('static', exist_ok=True)

# Function to get coordinates using Nominatim OpenStreetMap API
def get_coordinates(location_name, state="Telangana", country="India"):
    """Get coordinates for a location using Nominatim OpenStreetMap API"""
    print(f"🔍 Geocoding: {location_name}...", end="", flush=True)
    
    base_url = "https://nominatim.openstreetmap.org/search"
    
    # Append state and country for better results
    query = f"{location_name}, {state}, {country}"
    
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
    }
    
    # Add a user-agent to comply with Nominatim usage policy
    headers = {
        "User-Agent": "TelanganaDistrict_CrimeMap/1.0"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        # If we got results, return the first one's coordinates
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f" ✅ Found: [{lat}, {lon}]")
            return [lat, lon]
        else:
            print(f" ❌ Not found")
            return None
    except Exception as e:
        print(f" ❌ Error: {str(e)[:50]}...")
        return None

def process_crime_data(pdf_path):
    # Hard-coded coordinates for districts in Telangana (2020-2022)
    manual_coords = {
        "Adilabad": [19.6641, 78.5320],
        "Bhadradri Kothagudem": [17.5555, 80.6190],
        "Hyderabad": [17.3850, 78.4867],
        "Jagtial": [18.7947, 78.9138],
        "Jangaon": [17.7250, 79.1520],
        "Jayashankar Bhupalpalli": [18.1973, 79.9383],
        "Jogulamba Gadwal": [16.2342, 77.8062],
        "Kamareddy": [18.3219, 78.3410],
        "Karimnagar": [18.4392, 79.1288],
        "Khammam": [17.2473, 80.1514],
        "Komaram Bheem Asifabad": [19.3647, 79.2798],
        "Mahabubabad": [17.6033, 80.0021],
        "Mahabubnagar": [16.7375, 77.9803],
        "Mancherial": [18.8741, 79.4637],
        "Medak": [18.0453, 78.2608],
        "Medchal-Malkajgiri": [17.5409, 78.4891],
        "Mulugu": [18.1972, 80.1846],
        "Nagarkurnool": [16.4822, 78.3245],
        "Nalgonda": [17.0583, 79.2671],
        "Narayanpet": [16.7452, 77.4954],
        "Nirmal": [19.0965, 78.3441],
        "Nizamabad": [18.6730, 78.1000],
        "Peddapalli": [18.6150, 79.3742],
        "Rajanna Sircilla": [18.3866, 78.8318],
        "Rangareddy": [17.3026, 78.3641],
        "Sangareddy": [17.6291, 78.0938],
        "Siddipet": [18.1019, 78.8521],
        "Suryapet": [17.1449, 79.6339],
        "Vikarabad": [17.3384, 77.9045],
        "Wanaparthy": [16.3679, 77.8121],
        "Warangal": [17.9784, 79.5910],
        "Yadadri Bhuvanagiri": [17.5083, 78.8824],
        "Cyberabad Commissionerate": [17.4949, 78.3995],
        "Rachakonda Commissionerate": [17.3000, 78.6000],
        "Secunderabad RP": [17.4399, 78.4983],
    }
    
    # Extract data from PDF
    print("📊 Extracting crime data from PDF...")
    district_data = []
    
    # For testing without PDF, generate sample data
    if pdf_path is None or not os.path.exists(pdf_path):
        print("⚠️ PDF not found, using sample data")
        sample_districts = [
            ["", "Adilabad", "", "", "", "", "", "", "", "4261"],
            ["", "Bhadradri Kothagudem", "", "", "", "", "", "", "", "6198"],
            ["", "Hyderabad", "", "", "", "", "", "", "", "46258"],
            ["", "Jagtial", "", "", "", "", "", "", "", "3820"],
            ["", "Jangaon", "", "", "", "", "", "", "", "2689"],
            ["", "Jayashankar Bhupalpally", "", "", "", "", "", "", "", "2355"],
            ["", "Jogulamba Gadwal", "", "", "", "", "", "", "", "1948"],
            ["", "Kamareddy", "", "", "", "", "", "", "", "2902"],
            ["", "Karimnagar", "", "", "", "", "", "", "", "5978"],
            ["", "Khammam", "", "", "", "", "", "", "", "7317"],
            ["", "Komaram Bheem Asifabad", "", "", "", "", "", "", "", "3589"],
            ["", "Mahabubabad", "", "", "", "", "", "", "", "3025"],
            ["", "Mahabubnagar", "", "", "", "", "", "", "", "5120"],
            ["", "Mancherial", "", "", "", "", "", "", "", "4415"],
            ["", "Medak", "", "", "", "", "", "", "", "4365"],
            ["", "Medchal-Malkajgiri", "", "", "", "", "", "", "", "12437"],
            ["", "Mulugu", "", "", "", "", "", "", "", "2198"],
            ["", "Nagarkurnool", "", "", "", "", "", "", "", "4319"],
            ["", "Nalgonda", "", "", "", "", "", "", "", "6875"],
            ["", "Narayanpet", "", "", "", "", "", "", "", "2131"],
            ["", "Nirmal", "", "", "", "", "", "", "", "3252"],
            ["", "Nizamabad", "", "", "", "", "", "", "", "5941"],
            ["", "Peddapalli", "", "", "", "", "", "", "", "3778"],
            ["", "Rajanna Sircilla", "", "", "", "", "", "", "", "3124"],
            ["", "Rangareddy", "", "", "", "", "", "", "", "15978"],
            ["", "Sangareddy", "", "", "", "", "", "", "", "7951"],
            ["", "Siddipet", "", "", "", "", "", "", "", "5125"],
            ["", "Suryapet", "", "", "", "", "", "", "", "5921"],
            ["", "Vikarabad", "", "", "", "", "", "", "", "4065"],
            ["", "Wanaparthy", "", "", "", "", "", "", "", "3458"],
            ["", "Warangal", "", "", "", "", "", "", "", "8751"],
            ["", "Yadadri Bhuvanagiri", "", "", "", "", "", "", "", "4589"],
            ["", "Cyberabad Commissionerate", "", "", "", "", "", "", "", "59911"],
            ["", "Rachakonda Commissionerate", "", "", "", "", "", "", "", "50348"],
            ["", "Secunderabad RP", "", "", "", "", "", "", "", "1470"],
        ]
        district_data = sample_districts
    else:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in range(29, 36):  # Extracts pages 29 to 35
                page = pdf.pages[page_num]
                tables = page.extract_table()
                if tables:
                    print(f"✅ Extracting Table from Page {page_num+1}")
                    for row in tables:
                        district_data.append(row)
    
    # Convert extracted data into DataFrame
    df = pd.DataFrame(district_data)
    
    # Select only relevant columns: District Name (Col 1) & Total Crimes (Col 9)
    df = df.iloc[:, [1, 9]]  # Keep only the relevant columns
    df.columns = ["District", "Total Crimes"]  # Rename columns
    
    # Remove header rows and empty values
    df = df.iloc[2:]  # Remove first 2 rows (headers)
    df = df.dropna()  # Drop empty rows
    
    # Convert crime numbers to integers
    df["Total Crimes"] = pd.to_numeric(df["Total Crimes"], errors="coerce")
    df = df.dropna()  # Drop rows where conversion failed
    
    # Clean district names (strip whitespace)
    df["District"] = df["District"].str.strip()
    
    # Remove the "TOTAL" row
    df = df[~df["District"].str.upper().isin(["TOTAL"])]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["District"])
    
    # List to store district crime data
    districts_with_coords = []
    
    # Process districts
    for index, row in df.iterrows():
        district = row["District"]
        crime_count = int(row["Total Crimes"])
        
        # First check manual coordinates
        if district in manual_coords:
            coords = manual_coords[district]
            print(f"📍 Using manual coordinates for {district}: {coords}")
        else:
            # Try geocoding
            coords = get_coordinates(district)
            time.sleep(0.5)  # Respect rate limits
        
        if coords:
            lat, lon = coords
            districts_with_coords.append({
                "district": district,
                "crimeCount": crime_count,
                "latitude": lat,
                "longitude": lon
            })
        else:
            print(f"⚠️ Warning: Could not geocode {district}")
    
    return districts_with_coords

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/crime-data')
def crime_data():
    # Path to your PDF file - change this to the actual path or set to None to use sample data
    pdf_path = None #r"C:\Users\kp\Downloads\Telangana_CrimeRates.pdf"
    
    # Process crime data
    districts = process_crime_data(pdf_path)
    
    # Return JSON response
    return jsonify(districts)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
        # Enhanced version of the get_coordinates function to be more robust
def get_coordinates_by_address(address, state="Telangana", country="India"):
    """Get coordinates for an address string using Nominatim OpenStreetMap API"""
    print(f"🔍 Geocoding address: {address}...", end="", flush=True)
    
    base_url = "https://nominatim.openstreetmap.org/search"
    
    # Append state and country for better results
    query = f"{address}, {state}, {country}"
    
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
    }
    
    # Add a user-agent to comply with Nominatim usage policy
    headers = {
        "User-Agent": "TelanganaDistrict_CrimeMap/1.0"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        # If we got results, return the first one's coordinates
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f" ✅ Found: [{lat}, {lon}]")
            return [lat, lon]
        else:
            print(f" ❌ Not found")
            return None
    except Exception as e:
        print(f" ❌ Error: {str(e)[:50]}...")
        return None

# Add a route to get nearest districts based on user location
@app.route('/api/nearby-districts')
def nearby_districts():
    try:
        # Get user coordinates from request parameters
        user_lat = float(request.args.get('lat'))
        user_lng = float(request.args.get('lng'))
        
        # Process crime data to get all district data
        pdf_path =None # r"C:\Users\kp\Downloads\TELANGANA STATE CRIME STATEMENT.pdf"
        all_districts = process_crime_data(pdf_path)
        
        # Calculate distance to each district
        for district in all_districts:
            district_lat = district['latitude']
            district_lng = district['longitude']
            
            # Simple distance calculation (Euclidean, not perfect but sufficient for basic proximity)
            # For more accuracy, Haversine formula would be better
            distance = ((user_lat - district_lat) ** 2 + (user_lng - district_lng) ** 2) ** 0.5
            district['distance'] = distance
        
        # Sort by distance
        nearby = sorted(all_districts, key=lambda x: x['distance'])
        
        # Return the 5 closest districts
        return jsonify(nearby[:5])
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Add a route to geocode an address
@app.route('/api/geocode')
def geocode_address():
    try:
        address = request.args.get('address')
        if not address:
            return jsonify({"error": "Address parameter is required"}), 400
            
        coordinates = get_coordinates_by_address(address)
        if coordinates:
            return jsonify({
                "success": True,
                "latitude": coordinates[0],
                "longitude": coordinates[1]
            })
        else:
            return jsonify({"success": False, "error": "Could not geocode the address"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Add a route to provide safety recommendations based on location
@app.route('/api/safety-tips')
def safety_recommendations():
    try:
        # Get user coordinates and nearby district
        user_lat = float(request.args.get('lat'))
        user_lng = float(request.args.get('lng'))
        district_name = request.args.get('district')
        
        # Process crime data to get risk level
        pdf_path = None  # r"C:\Users\kp\Downloads\TELANGANA STATE CRIME STATEMENT.pdf"
        all_districts = process_crime_data(pdf_path)
        
        # Find the district by name
        district_data = next((d for d in all_districts if d['district'].lower() == district_name.lower()), None)
        
        if district_data:
            crime_count = district_data['crimeCount']
            
            # Determine risk level
            if crime_count > 1000:
                risk_level = "high"
                tips = [
                    "Avoid traveling alone, especially at night",
                    "Keep valuables secure and out of sight",
                    "Stay in well-lit and populated areas",
                    "Share your live location with family members",
                    "Keep emergency contacts easily accessible"
                ]
            elif crime_count >= 5000:
                risk_level = "moderate"
                tips = [
                    "Be aware of your surroundings",
                    "Avoid displaying expensive items in public",
                    "Travel in groups when possible",
                    "Keep your phone charged for emergencies",
                    "Know the nearest police stations"
                ]
            else:
                risk_level = "low"
                tips = [
                    "Basic precautions are still recommended",
                    "Keep emergency contact numbers handy",
                    "Be cautious in unfamiliar areas",
                    "Lock vehicles and homes securely",
                    "Report any suspicious activities"
                ]
            
            return jsonify({
                "district": district_name,
                "riskLevel": risk_level,
                "crimeCount": crime_count,
                "safetyTips": tips
            })
        else:
            return jsonify({"error": "District not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# When running the app, make it more production-ready
if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create HTML template (your existing code for this)
    
    # Add better error logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='app.log'
    )
    
    print("🚀 Starting Safe City - Telangana application...")
    print("📊 Crime data will be loaded on first request")
    print("📱 Access the application at http://127.0.0.1:5000")
    app.run(debug=True)
