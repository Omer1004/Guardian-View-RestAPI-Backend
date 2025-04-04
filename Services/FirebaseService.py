import logging
import os
import threading
from multiprocessing import Process, Event
import time
import firebase_admin
from firebase_admin import auth, credentials, firestore, storage
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Singleton class for FirebaseService
class FirebaseService:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance.initialize_firebase()
        return cls._instance

    def initialize_firebase(self):
        # Initialize Firebase Admin SDK with credentials
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        self.cred = credentials.Certificate(cred_path)
        self.settings_doc_id = os.getenv("FIREBASE_SETTINGS_DOC_ID")  # The ID of the single document in the settings collection
        self.live_detection_active = False
        self.storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")

        if not firebase_admin._apps:
            firebase_admin.initialize_app(self.cred, {
                'storageBucket': self.storage_bucket
            })

        # Firestore client
        self.db = firestore.client()
        
        # Firebase Storage
        self.bucket = storage.bucket(self.storage_bucket)

        logging.info("FirebaseService initialized with Firestore and Storage")

        
    def setVideoProcessingService(self, video_processing_service):
        self.video_processing_service = video_processing_service
        self.listen_to_user_videos()
        self.listen_to_settings()
        logging.info("VideoProcessingService set for FirebaseService")
    
    
    def __init__(self):
        pass
        
        


    ##################### AUTHENTICATION METHODS ##########################################
        
    def create_user(self, email, password):
        """Create a new user with email and password."""
        user = auth.create_user(email=email, password=password)
        logging.info(f"User created with email: {email}")
        return user

    def delete_user(self, uid):
        """Delete a user identified by uid."""
        auth.delete_user(uid)
        logging.info(f"User deleted with UID: {uid}")
        return True



    ##################### DATABASE METHODS ##############################

    def log_error(self, error_message):
        error_data = {
            'timestamp': firestore.SERVER_TIMESTAMP,
            'error_message': error_message,
        }
        self.db.collection('errors').add(error_data)
        logging.info("Error logged to Firestore")


   
    def add_document(self, collection_name, document_data):
        """Add a document to a specified Firestore collection."""
        doc_ref = self.db.collection(collection_name).add(document_data)
        logging.info(f"Document added to {collection_name} collection")
        return doc_ref
    
    def add_alert(self, collection_name, alert_data):
        """Add a document to a specified Firestore collection with a specific ID."""
        document_id = alert_data.get('id')
        doc_ref = self.db.collection(collection_name).document(document_id)
        doc_ref.set(alert_data)
        logging.info(f"Document {document_id} added to {collection_name} collection")
        return doc_ref

    def get_document(self, collection_name, document_id):
        """Retrieve a document from a specified Firestore collection."""
        doc = self.db.collection(collection_name).document(document_id).get()
        logging.info(f"Document retrieved from {collection_name} with ID: {document_id}")
        return doc if doc.exists else None
    


##################### LISTENERS ##########################################

    def listen_to_user_videos(self):
        logging.info("Setting up video analysis listener to Firestore...")
        
        # Define the callback function to capture changes
        def on_snapshot(doc_snapshot, changes, read_time):
            logging.info(f"New changes in videos_from_user collection: {changes}")
            for change in changes:
                if change.type.name == 'ADDED':
                    video_doc = change.document
                    video_id = video_doc.id
                    video_data = video_doc.to_dict()

                    if not video_data.get('processed', False):  # Check if the video is already processed
                        video_url = video_data.get('URL')
                        logging.info(f"New video added: {video_url}")

                        # Check if the URL is a stream or a download link
                        if 'firebasestorage.googleapis.com' in video_url and 'alt=media' not in video_url:
                            video_url += '&alt=media'

                        # Process the video in a separate thread
                        threading.Thread(target=self.process_video, args=(video_url, video_id)).start()

        # Reference to the 'videos_from_user' collection
        collection_ref = self.db.collection("videos_from_user")

        # Watch the collection for changes
        collection_ref.on_snapshot(on_snapshot)

        logging.info("Video analysis listener set up complete")

    def process_video(self, video_url, video_id):
        try:
            local_video_path = self.download_video(video_url)
            logging.info(f"Downloaded video to {local_video_path}")
            self.video_processing_service.video_analysis(local_video_path, videoURL=video_url)
            logging.info("Video processing completed successfully")
            self.update_document("videos_from_user", video_id, {"processed": True})
            logging.info(f"Video {video_id} marked as processed")
            os.remove(local_video_path)
        except Exception as e:
            logging.error(f"Error processing video {video_url}: {str(e)}")

    def listen_to_settings(self):
        logging.info("Setting up settings listener to Firestore...")
        
        settings_doc_id = self.settings_doc_id 
        
        # Define the callback function to capture changes in settings
        def on_snapshot(doc_snapshot, changes, read_time):
            for change in changes:
                if change.type.name in ['ADDED', 'MODIFIED']:
                    settings_doc = change.document
                    settings_data = settings_doc.to_dict()
                    threashold = settings_data.get('threshHold', 0.6)
                    if threashold:
                        if threashold < 0.4 or threashold > 1:
                            self.video_processing_service.confidence_threshold = 0.6
                            logging.error(f"Invalid confidence threshold value: {threashold}. Defaulting to 0.6")
                        else:
                            self.video_processing_service.confidence_threshold = threashold
                            logging.info(f"Confidence threshold updated to {threashold}")
                    live_detection = settings_data.get('isLive', False)

                    if live_detection and not self.live_detection_active:
                        self.start_live_detection()
                    elif not live_detection and self.live_detection_active:
                        self.stop_live_detection()

        # Reference to the single document in the 'settings' collection
        doc_ref = self.db.collection("settings").document(settings_doc_id)

        # Watch the document for changes
        doc_ref.on_snapshot(on_snapshot)

    #those functions require work and are not finished yet
    def start_live_detection(self):
        #self.stop_event = Event()
        #self.live_detection_process = Process(target=self.run_live_detection, args=())
        #self.live_detection_process.start()
        #self.video_processing_service.live_video_analysis()
        self.live_detection_active = True
        logging.info("Live video analysis process started")

    def stop_live_detection(self):
        #if self.live_detection_process:
        #    self.stop_event.set()
        #    self.live_detection_process.join()
        logging.info("Live video analysis process stopped")
        self.video_processing_service.stop_live_video_analysis()
        settings_doc_id = self.settings_doc_id  # The ID of the single document in the settings collection
        self.live_detection_active = False
        self.update_document("settings", settings_doc_id, {"isLive": False})

    

    def run_live_detection(self):
        try:
            self.video_processing_service.live_video_analysis()
        except Exception as e:
            logging.error(f"Error during live video analysis: {str(e)}")
            self.log_error(f"Error during live video analysis: {str(e)}")
            # Set 'isLive' to False in Firestore in case of error
            settings_doc_id = self.settings_doc_id  # The ID of the single document in the settings collection
            self.live_detection_active = False
            self.update_document("settings", settings_doc_id, {"isLive": False})





    def download_video(self, video_url):
        try:
            logging.info(f"Downloading video from {video_url}")
            local_filename = video_url.split('/')[-1].split('?')[0]
            local_filepath = os.path.join('/Users/wmryny/Desktop/לימודים/פרוייקט גמר/FinalProject/GuardianViewRest/Videos_from_user', local_filename)
            
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(local_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logging.info(f"Video downloaded to {local_filepath}")
            return local_filepath

        except Exception as e:
            logging.error(f"Error downloading video {video_url}: {str(e)}")
            raise

    def update_document(self, collection_name, document_id, update_data):
        """Update a document in a specified Firestore collection."""
        doc_ref = self.db.collection(collection_name).document(document_id)
        doc_ref.update(update_data)
        logging.info(f"Document {document_id} updated in {collection_name} collection")

    
    ##################### STORAGE METHODS ##################################

    def download_file(self, blob_name, destination_file_path):
        """Download a file from Firebase Storage."""
        blob = self.bucket.blob(blob_name)
        blob.download_to_filename(destination_file_path)
        logging.info(f"File downloaded from Storage: {blob_name} to {destination_file_path}")


    def upload_frame(self, filepath, filename):
        """Upload a frame to Firebase Storage and return the public URL."""
        # Construct the full path for the blob
       
        blob = self.bucket.blob(f'detections/{filename}')

        # Upload the file to Firebase Storage
        blob.upload_from_filename(filepath)
        
        # Make the blob publicly accessible
        blob.make_public()
        

        # Get the public URL of the file
        image_url = blob.public_url
        logging.info(f"Frame uploaded to Storage as {filename} with URL {image_url}")

        return image_url


    def download_video_from_firebase(storage_url):
        # Assuming `storage_url` is thehe URL to the video in Firebase Storage
        # Use Firebase SDK or appropriate method to download the video file
        
        video_path = 'local_path_to_downloaded_video.mp4'
        # Code to download the video and save it to `video_path`
        return video_path

    def test_upload(self):
            # Full path to the file you want to upload
            filepath = 'Results/gun_17_2024-03-21_15-50-21.jpg'
            filename = 'gun_17_2024-03-21_15-50-21.jpg'
            
            logging.info(f"Testing upload of {filename} to Firebase Storage")
            # Use the existing upload_frame method to upload the file
            image_url = self.upload_frame(filepath, filename)

            logging.info(f"File {filename} uploaded to Storage with URL {image_url}")

            return image_url








##############################    UTILS     #################################################################





##############################################################################################################


# Usage Example
# firebase_service = FirebaseService()
# firebase_service.add_document('collection_name', {'key': 'value'})
# firebase_service.upload_file('local_file_path', 'remote_blob_name')


