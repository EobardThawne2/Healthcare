import os
from flask import Flask, request, jsonify, render_template
from geopy.distance import geodesic

app = Flask(__name__)

# Hospital list - add your complete hospital data here
hospitals_details = [
    {
        'name': 'All India Institute of Medical Sciences (AIIMS)',
        'coords': (28.56586, 77.20781),
        'specialties': ['general', 'trauma', 'cardiac', 'orthopedic', 'neuro']
    },
    {
        'name': 'Fortis Hospital, Vasant Kunj',
        'coords': (28.52734, 77.15155),
        'specialties': ['general', 'cardiac', 'orthopedic']
    },
    {
        'name': 'Indraprastha Apollo Hospitals, Jasola',
        'coords': (28.54179, 77.28326),
        'specialties': ['general', 'cardiac', 'trauma', 'neuro']
    },
    {
        'name': 'Sir Ganga Ram Hospital, Rajinder Nagar',
        'coords': (28.63981, 77.18866),
        'specialties': ['general', 'orthopedic']
    },
    {
        'name': 'Max Super Speciality Hospital, Saket',
        'coords': (28.51918, 77.21301),
        'specialties': ['general', 'cardiac', 'orthopedic', 'neuro']
    },
    {
        'name': 'Medanta – The Medicity, Gurgaon',
        'coords': (28.45, 77.03),
        'specialties': ['general', 'cardiac', 'trauma', 'neuro', 'orthopedic']
    },
    {
        'name': 'BLK Super Speciality Hospital, Pusa Road',
        'coords': (28.64435, 77.19161),
        'specialties': ['general', 'cardiac', 'orthopedic', 'neuro']
    },
    {
        'name': 'Moolchand Hospital, Lajpat Nagar IV',
        'coords': (28.5656, 77.2346),
        'specialties': ['general', 'cardiac', 'orthopedic']
    },
    {
        'name': 'Artemis Hospital, Vasant Kunj',
        'coords': (28.52734, 77.15155),
        'specialties': ['general', 'orthopedic']
    },
    {
        'name': 'Safdarjung Hospital, Ansari Nagar East',
        'coords': (28.5659, 77.2078),
        'specialties': ['general', 'trauma', 'cardiac']
    }
]

@app.route("/")
def index():
    return render_template("test.html")

@app.route("/secondary")
def secondary():
    return render_template("index SECONDARY.html")

@app.route("/hospitals")
def hospitals_list():
    return render_template("hlist.html", hospitals=hospitals_details)

@app.route("/get-directions", methods=["GET"])
def get_direction_url():
    try:
        lat = request.args.get("lat", type=float)
        lng = request.args.get("lng", type=float)
        injuries = request.args.get("injuries", type=str)
        bp = request.args.get("bp", type=str)
        pulse = request.args.get("pulse", type=str)
        injury_location = request.args.get("injury_location", type=str)

        if lat is None or lng is None:
            return jsonify({"error": "Missing or invalid latitude/longitude"}), 400

        ambulance_location = (lat, lng)

        specialization_needed = None

        # BP triage logic
        if bp:
            try:
                systolic_str, diastolic_str = bp.split("/")
                systolic = int(systolic_str.strip())
                diastolic = int(diastolic_str.strip())
                if systolic < 90 or diastolic < 60:
                    specialization_needed = "cardiac"
                elif systolic >= 180 or diastolic >= 120:
                    specialization_needed = "cardiac"
                elif systolic >= 140 or diastolic >= 90:
                    specialization_needed = "cardiac"
            except:
                pass

        # Injury location/body part triage
        if injury_location:
            iloc = injury_location.lower()
            if "head" in iloc or "brain" in iloc:
                specialization_needed = "neuro"
            elif "leg" in iloc or "arm" in iloc or "fracture" in iloc:
                specialization_needed = "orthopedic"
            elif "chest" in iloc:
                if specialization_needed is None:
                    specialization_needed = "trauma"

        # Injury type triage fallback
        if not specialization_needed and injuries:
            injuries_lower = injuries.lower()
            if "trauma" in injuries_lower:
                specialization_needed = "trauma"
            elif "cardiac" in injuries_lower:
                specialization_needed = "cardiac"
            elif "orthopedic" in injuries_lower:
                specialization_needed = "orthopedic"
            elif "neuro" in injuries_lower:
                specialization_needed = "neuro"

        # Filter hospitals by specialization
        if specialization_needed:
            possible_hospitals = [h for h in hospitals_details if specialization_needed in h["specialties"]]
            if not possible_hospitals:
                possible_hospitals = hospitals_details
        else:
            possible_hospitals = hospitals_details

        nearest_hospital = min(
            possible_hospitals,
            key=lambda h: geodesic(ambulance_location, h["coords"]).km
        )

        url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={lat},{lng}"
            f"&destination={nearest_hospital['coords'][0]},{nearest_hospital['coords'][1]}"
            f"&travelmode=driving"
        )

        # Severity calculation based on BP
        severity = None
        if bp:
            try:
                systolic_str, diastolic_str = bp.split("/")
                systolic = int(systolic_str.strip())
                diastolic = int(diastolic_str.strip())
                if systolic < 90 or diastolic < 60:
                    severity = "critical"
                elif systolic >= 180 or diastolic >= 120:
                    severity = "critical"
                elif systolic >= 140 or diastolic >= 90:
                    severity = "high"
                else:
                    severity = "normal"
            except:
                severity = "unknown"

        return jsonify({
            "maps_url": url,
            "hospital": nearest_hospital["name"],
            "selected_specialization": specialization_needed or "nearest/unspecified",
            "bp": bp,
            "pulse": pulse,
            "injury": injuries,
            "injury_location": injury_location,
            "severity": severity
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(debug=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)