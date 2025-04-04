import datetime
import json
import logging
import random
import uuid
from google.cloud import firestore

# JSON data
json_data = '''
{
  "coordinates": [
    {"id": 1, "lat": 31.7767, "lon": 35.2345, "name": "Jerusalem 1"},
    {"id": 2, "lat": 31.7768, "lon": 35.2346, "name": "Jerusalem 2"},
    {"id": 3, "lat": 31.7766, "lon": 35.2344, "name": "Jerusalem 3"},
    {"id": 4, "lat": 32.0853, "lon": 34.7818, "name": "Tel Aviv"},
    {"id": 5, "lat": 31.8969, "lon": 34.8186, "name": "Beit Shemesh"},
    {"id": 6, "lat": 32.1840, "lon": 34.8697, "name": "Petah Tikva"},
    {"id": 7, "lat": 31.9628, "lon": 34.8061, "name": "Ramla"},
    {"id": 8, "lat": 32.0714, "lon": 34.8242, "name": "Givatayim"},
    {"id": 9, "lat": 31.9946, "lon": 34.7589, "name": "Rishon LeZion"},
    {"id": 10, "lat": 32.0852, "lon": 34.9780, "name": "Rosh HaAyin"},
    {"id": 11, "lat": 32.0751, "lon": 34.7752, "name": "Dizengoff Center"},
    {"id": 12, "lat": 32.1001, "lon": 34.7745, "name": "Tel Aviv Port"},
    {"id": 13, "lat": 32.0724, "lon": 34.7794, "name": "Habima Square"},
    {"id": 14, "lat": 32.0684, "lon": 34.7684, "name": "Carmel Market"},
    {"id": 15, "lat": 32.0526, "lon": 34.7519, "name": "Jaffa Old City"},
    {"id": 16, "lat": 32.0998, "lon": 34.8080, "name": "Yarkon Park"},
    {"id": 17, "lat": 32.0778, "lon": 34.7868, "name": "Tel Aviv Museum of Art"},
    {"id": 18, "lat": 32.0652, "lon": 34.7765, "name": "Rothschild Boulevard"},
    {"id": 19, "lat": 32.0632, "lon": 34.7665, "name": "Neve Tzedek"},
    {"id": 20, "lat": 32.0744, "lon": 34.7923, "name": "Azrieli Center"},
    {"id": 21, "lat": 32.1118, "lon": 34.8014, "name": "Tel Aviv University"}
  ]
}
'''

class LocationSelector:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LocationSelector, cls).__new__(cls)
        return cls._instance

    def __init__(self, json_data):
        if not hasattr(self, 'initialized'):
            self.original_data = json.loads(json_data)
            self.reset()
            self.initialized = True

    def reset(self):
        self.available_coordinates = self.original_data['coordinates'].copy()

    def select_random_location(self):
        if not self.available_coordinates:
            print("All locations have been selected. Resetting the list.")
            self.reset()

        selected = random.choice(self.available_coordinates)
        self.available_coordinates = [coord for coord in self.available_coordinates if coord['id'] != selected['id']]
        logging.info(f"Selected random location: {selected}")
        return selected

class AlertManagementService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AlertManagementService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.selector = LocationSelector(json_data)
            self.initialized = True

    def generate_alert(self, class_name, conf, image_url, source, video_path=None, severity="Low"):
        # Generate a unique ID for the alert
        alert_id = str(uuid.uuid4())

        # Determine location based on source
        if source == 'live_video':
            location = {"name": "Afeka College", "lon": 34.8175, "lat": 32.1134}
        else:
            location = self.selector.select_random_location()

        # Create alert data
        alert_data = {
            "id": alert_id,
            "alertType": class_name,
            "source": source,
            "description": f"A potential {class_name} was detected in the video.",
            "videoUrl": video_path,
            "imageUrl": image_url,
            "severity": severity,
            "longitude": location["lon"],
            "latitude": location["lat"],
            "location": location["name"],
            "confidence": conf,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "isConfirmed": False
        }

        logging.info(f"Alert created: {alert_data}")
        return alert_data
