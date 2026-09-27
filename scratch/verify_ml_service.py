import sys
sys.path.insert(0, 'backend')
from services.ml_service import ml_service
from services.dataset_service import dataset_service

test_cases = [
    ('User Coord 1 (Sausar Belt)', 21.9717, 79.5238),
    ('User Coord 2 (Karnataka Chitradurga)', 14.4083, 76.1250),
    ('Balaghat Mine', 21.8487, 80.2359),
    ('Ukwa Mine', 21.9619, 80.4698),
    ('Tirodi Mine', 21.6836, 79.7468),
    ('Joda West (Odisha)', 22.0100, 85.4100),
    ('Kasia (Odisha)', 22.0620, 85.4350),
    ('Sandur Deogiri (Karnataka)', 15.0530, 76.5820),
    ('Adilabad Tamsi (Telangana)', 19.6912, 78.4115),
    ('Garividi (Andhra Pradesh)', 18.2830, 83.5330),
    ('Rivona (Goa)', 15.1900, 74.1100),
    ('Tambesra (Rajasthan)', 23.2000, 74.3600),
    ('Mumbai (Coastal Non-ore)', 19.0760, 72.8770),
    ('Delhi (North Plains Non-ore)', 28.6139, 77.2090),
    ('Kolkata (Delta Non-ore)', 22.5726, 88.3639),
    ('Jaipur (Plains Non-ore)', 26.9124, 75.7873),
]

print('=' * 85)
print('VERIFYING CALIBRATED ML PREDICTIONS ACROSS INDIA')
print('=' * 85)

for name, lat, lon in test_cases:
    is_ore_area = any(k in name for k in ['User', 'Mine', 'Odisha', 'Karnataka', 'Telangana', 'Andhra', 'Goa', 'Rajasthan'])
    ndvi_val = 0.22 if is_ore_area else 0.05
    elev_val = 450.0 if is_ore_area else 12.0
    slope_val = 5.5 if is_ore_area else 1.2
    
    res = ml_service.predict_manganese_potential(lat, lon, features={
        'Blue_B02': 0.18, 'Green_B03': 0.21, 'Red_B04': 0.25,
        'NIR_B08': 0.38, 'SWIR1_B11': 0.40, 'SWIR2_B12': 0.35,
        'NDVI': ndvi_val,
        'Lithology': 'Metamorphics', 'GLiM_ID': 'IND2497',
        'Elevation_mean_m': elev_val,
        'Elevation_min_m': elev_val - 15.0,
        'Elevation_max_m': elev_val + 35.0,
        'Slope_mean_degrees': slope_val,
        'Slope_min_degrees': 1.0, 'Slope_max_degrees': 18.0,
        'LST_mean_C': 32.0, 'LST_min_C': 30.5, 'LST_max_C': 33.8,
        '_gee_metadata': {'start_date': '2026-02-01', 'end_date': '2026-05-31'}
    })
    dep = dataset_service.find_nearest_ore_deposit(lat, lon, max_distance_km=35.0)
    dep_msg = dep['message'] if dep else 'None within 35km'
    print(f"{name:<35} ({lat:7.4f}, {lon:7.4f}) -> {res['potential']:<16} ({res['probability_percentage']:4.1f}%) | Near: {dep_msg}")
    print(f"   Key Factors: {res['key_factors']}")
    print('-' * 85)
