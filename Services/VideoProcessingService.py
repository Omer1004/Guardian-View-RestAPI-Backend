import logging
import threading
import time
import cv2
from ultralytics import YOLO
import datetime
from Services.AlertManagementService import AlertManagementService


class VideoProcessingService:
    def __init__(self, firebase_service):
        self.firebase_service = firebase_service
        logging.basicConfig(level=logging.INFO)
        
        self.model_path = {"yolov8s":'WeaponsDetection/guardianViewV5.pt',"yolov8m":'WeaponsDetection/guardianViewV2.pt'}
        self.model = YOLO(self.model_path.get("yolov8s"))
        self.modelLive = YOLO(self.model_path.get("yolov8m"))
        self.confidenceThreshold = 0.6
        self.model_names = ['gun', 'knife', 'person']
        self.stop_event = None
        self.alert_management_service = AlertManagementService()

 
    # This function processes user-uploaded videos by analyzing each frame using the YOLO model.
    # It identifies threats such as guns and knives, logging the highest confidence detections.
    # The function generates alerts if threats are detected consistently for a specified number of frames (required_consistent_frames).
    # This version selects the frame with the highest confidence in the longest streak of consistent detections for alert generation.
    def video_analysis_longest_streak(self, video_path, showAnalysis=False, videoURL=None, location='Tel Aviv', longitud=32.114414, latitude=34.817955):
        logging.info(f"Starting video analysis for {video_path}")

        try:
            confidenceThreshold = self.confidenceThreshold
            results = self.model.predict(video_path, conf=confidenceThreshold, stream=True, show=showAnalysis)
            max_conf = 0
            best_frame = None
            frame_idx = 0
            total_frames = 0
            consistent_detections = 0
            streak_best_frame = None
            streak_max_conf = 0
            max_consistent_detections = 0
            longest_streak_best_frame = None
            required_consistent_frames = 3  # Number of consistent detections required to trigger an alert

            logging.info(f"Processing video {video_path}")

            for r in results:
                total_frames += 1
                logging.info(f"Processing frame {frame_idx}")

                if not hasattr(r, 'boxes') or r.boxes is None:
                    logging.info(f"No boxes found in frame {frame_idx}")
                    frame_idx += 1
                    continue

                xyxy = r.boxes.xyxy.numpy()  # Bounding box coordinates as numpy array
                confs = r.boxes.conf.numpy()  # Confidence scores as numpy array
                classes = r.boxes.cls.numpy()  # Class indices as numpy array
                frame_threats = False

                for bbox, conf, cls_idx in zip(xyxy, confs, classes):
                    if conf >= confidenceThreshold and cls_idx in [0, 1]:
                        class_name = self.model.names[int(cls_idx)]
                        if self.is_valid_bbox(bbox, r.orig_shape):
                            logging.info(f"Detected {class_name} with confidence {conf}")
                            frame_threats = True

                            if conf > streak_max_conf:
                                streak_max_conf = conf
                                streak_best_frame = {'result': r, 'frame_idx': frame_idx, 'conf': conf, 'class_name': class_name, 'boxes': xyxy}

                if frame_threats:
                    consistent_detections += 1
                    if consistent_detections >= required_consistent_frames:
                        if consistent_detections > max_consistent_detections:
                            max_consistent_detections = consistent_detections
                            longest_streak_best_frame = streak_best_frame
                else:
                    consistent_detections = 0
                    streak_max_conf = 0
                    streak_best_frame = None

                frame_idx += 1

            if total_frames == 0:
                logging.warning("No frames were processed. Please check the video input or format.")
            elif longest_streak_best_frame:
                if videoURL is not None:
                    self.save_frame_and_generate_alert(longest_streak_best_frame, 'video', videoURL)
                else:
                    self.save_frame_and_generate_alert(longest_streak_best_frame, 'video', video_path)
            else:
                logging.info("No valid frames detected with the required confidence threshold.")

        except Exception as e:
            logging.error(f"Error occurred during video analysis: {str(e)}")
            self.firebase_service.log_error(f"Error occurred during video analysis: {str(e)}")
            return


    # This function processes user-uploaded videos by analyzing each frame using the YOLO model.
    # It identifies threats such as guns and knives, logging the highest confidence detections.
    # The function generates alerts if threats are detected consistently for a specified number of frames (required_consistent_frames).
    # This version selects the frame with the highest confidence across the entire video for alert generation.
    def video_analysis(self, video_path, showAnalysis= False, videoURL=None,location='Tel Aviv',longitud=32.114414,latitude=34.817955):
        logging.info(f"Starting video analysis for {video_path}")

        try:
            confidenceThreshold = self.confidenceThreshold
            results = self.model.predict(video_path,conf= confidenceThreshold, stream=True, show=showAnalysis)
            max_conf = 0
            best_frame = None
            frame_idx = 0
            total_frames = 0
            consistent_detections = 0
            streak_best_frame = None
            streak_max_conf = 0
            max_consistent_detections = 0
            required_consistent_frames = 2  # Number of consistent detections required to trigger an alert

            logging.info(f"Processing video {video_path}")

            for r in results:
                total_frames += 1
                logging.info(f"Processing frame {frame_idx}")

                if not hasattr(r, 'boxes') or r.boxes is None:
                    logging.info(f"No boxes found in frame {frame_idx}")
                    frame_idx += 1
                    continue

                xyxy = r.boxes.xyxy.numpy()  # Bounding box coordinates as numpy array
                confs = r.boxes.conf.numpy()  # Confidence scores as numpy array
                classes = r.boxes.cls.numpy()  # Class indices as numpy array
                frame_threats = False

                for bbox, conf, cls_idx in zip(xyxy, confs, classes):
                    if conf >= confidenceThreshold and cls_idx in [0, 1]:
                        class_name = self.model.names[int(cls_idx)]
                        if self.is_valid_bbox(bbox, r.orig_shape):
                            logging.info(f"Detected {class_name} with confidence {conf}")
                            frame_threats = True

                            if conf > streak_max_conf:
                                streak_max_conf = conf
                                streak_best_frame = {'result': r, 'frame_idx': frame_idx, 'conf': conf, 'class_name': class_name, 'boxes': xyxy}

                if frame_threats:
                    consistent_detections += 1
                    if consistent_detections > max_consistent_detections:
                        max_consistent_detections = consistent_detections
                else:
                    consistent_detections = 0
                    streak_max_conf = 0
                    streak_best_frame = None

                if consistent_detections >= required_consistent_frames:
                    if streak_best_frame:
                        if streak_best_frame['conf'] > max_conf:
                            max_conf = streak_best_frame['conf']
                            best_frame = streak_best_frame

                frame_idx += 1
                

            if total_frames == 0:
                logging.warning("No frames were processed. Please check the video input or format.")
            elif best_frame:
                if videoURL is not None:
                    self.save_frame_and_generate_alert(best_frame, 'video', videoURL)
                else:
                    self.save_frame_and_generate_alert(best_frame, 'video', video_path)
            else:
                logging.info("No valid frames detected with the required confidence threshold.")
            

        except Exception as e:
            logging.error(f"Error occurred during video analysis: {str(e)}")
            self.firebase_service.log_error(f"Error occurred during video analysis: {str(e)}")
            return


    def is_valid_bbox(self, bbox, img_shape):
        """Check if the bounding box is less than 5/6 of the screen size."""
        img_height, img_width = img_shape[:2]
        bbox_width = bbox[2] - bbox[0]
        bbox_height = bbox[3] - bbox[1]
        

        if bbox_width / img_width <= 5/6 and bbox_height / img_height <= 5/6:
            return True
        logging.info(f"Invalid bounding box detected: {bbox}")
        return False


    # recive threashold from admin
    def determine_severity(self,conf, class_name):
        
        if conf >= 0.90:
            severity = "Emergency"
        elif conf >= 0.75:
            severity = "High"
        elif conf >= 0.65:
            severity = "Medium"
        elif conf >= 0.4:
            severity = "Low"
        else:
            severity = "Resolved"  # Assuming that confidence lower than 0.55 might be a false alarm or resolved
        
        # Additional logic to adjust severity based on class_name
        if class_name == "gun":
            if severity == "Low":
                severity = "Medium"
            elif severity == "Medium":
                severity = "High"
            elif severity == "High":
                severity = "Emergency"
        logging.info(f"Determined severity for {class_name} with confidence {conf}: {severity}")
        return severity




    def save_frame_and_generate_alert(self, frame, source, video_path=None,location='None',longitud=32.114414,latitude=34.817955):
        try:
            r = frame.get('result')
            class_name = frame.get('class_name')
            frame_idx = frame.get('frame_idx')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            local_filename = f"{class_name}_{frame_idx}_{timestamp}.jpg"
            local_filepath = f'Results/{local_filename}'
            severity = self.determine_severity(frame.get('conf'), class_name)
            
            # Save the frame locally
            r.save(local_filepath)
            logging.info(f"Saving frame for detected {class_name} with confidence {frame.get('conf')}")
            conf = float(frame.get('conf'))
            
            # Upload the frame to Firebase Storage
            image_url = self.firebase_service.upload_frame(local_filepath, local_filename)
            logging.info(f"Image URL: {image_url}")
            
            self.generateAlert(class_name, conf, image_url, timestamp, source, video_path, severity)
        except Exception as e:
            logging.error(f"Error occurred while saving frame and generating alert: {str(e)}")
            self.firebase_service.log_error(f"Error occurred while saving frame and generating alert: {str(e)}")
            return
        
    

    
    def generateAlert(self, class_name, conf, image_url, timestamp, source, video_path=None, severity="Low"):
        # Create alert data 
        alert_data = self.alert_management_service.generate_alert(class_name, conf, image_url, source, video_path, severity)
        # Save the alert to Firestore
        try:
            self.firebase_service.add_alert('alerts', alert_data)
            logging.info(f"Alert created and saved to Firestore: {alert_data}")
        except Exception as e:
            logging.error(f"Error occurred while saving alert to Firestore: {str(e)}")
            self.firebase_service.log_error(f"Error occurred while saving alert to Firestore: {str(e)}")
            return
    

    def stop_live_video_analysis(self):
        if self.stop_event:
            self.stop_event.set()
    
    
    '''
    this function has a problem with the cv2.imshow() and PIL Image.show() functions if runs in a thread if runs in the main class it works
    same for the video_analysis function it cant show the results in a thread only in the main class
    024-06-27 13:34:09.976 Python[37323:290249] WARNING: AVCaptureDeviceTypeExternal is deprecated for Continuity Cameras. Please use AVCaptureDeviceTypeContinuityCamera and add NSCameraUseContinuityCameraDeviceType to your Info.plist.
    WARNING ⚠️ Environment does not support cv2.imshow() or PIL Image.show()
    Unknown C++ exception from OpenCV code

    0: 384x640 1 person, 248.1ms
    Speed: 1.9ms preprocess, 248.1ms inference, 488.8ms postprocess per image at shape (1, 3, 384, 640)
    2024-06-27 13:34:12,458 - ERROR - Error during live video analysis: Unknown C++ exception from OpenCV code
    '''
        #when this function is started in a seperated class it works when started in the main class it doesnt work probably because of threads  
    def live_video_analysis(self, source=1, show=True):
        try:
            logging.info("Starting live video analysis")
            confidenceThreshold = self.confidenceThreshold
            self.stop_event = threading.Event()
            cap = cv2.VideoCapture(source)

            if not cap.isOpened():
                error_message = "Error: Could not open video stream."
                logging.error(error_message)
                return

            alert_active = False
            consistent_detections = 0
            streak_best_frame = None
            streak_max_conf = 0
            required_consistent_frames = 4  # Number of consistent detections required to trigger an alert
            last_detection_time = None
            cool_down_time = 5  # Minimum duration of no threat detection required to reset the alert state

            while cap.isOpened() and not self.stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    logging.error("Failed to read frame from video stream.")
                    break

                # Perform prediction on the current frame
                results = self.modelLive.predict(source=frame, conf=confidenceThreshold, show=show, stream=True)
                current_time = time.time()
                threat_detected = False

                for r in results:
                    xyxy = r.boxes.xyxy  # Bounding box coordinates
                    confs = r.boxes.conf  # Confidence scores
                    classes = r.boxes.cls  # Class indices
                    for conf, cls_idx, bbox in zip(confs, classes, xyxy):
                        if conf >= confidenceThreshold and cls_idx in [0, 1]:  # Assuming 0 and 1 are the class indices for threats
                            class_name = self.model.names[int(cls_idx)]
                            if self.is_valid_bbox(bbox, r.orig_shape):
                                logging.info(f"Detected {class_name} with confidence {conf}")
                                threat_detected = True

                                if conf > streak_max_conf:
                                    streak_max_conf = conf
                                    streak_best_frame = {'result': r, 'frame_idx': time.time(), 'conf': conf, 'class_name': class_name, 'boxes': xyxy}

                if threat_detected:
                    consistent_detections += 1
                    last_detection_time = current_time
                else:
                    consistent_detections = 0
                    streak_max_conf = 0
                    streak_best_frame = None

                if consistent_detections >= required_consistent_frames and not alert_active:
                    if streak_best_frame:
                        self.save_frame_and_generate_alert(
                            streak_best_frame,
                            'live_video'
                        )
                        alert_active = True
                        consistent_detections = 0  # Reset after triggering the alert
                        logging.info(f"Alert triggered for {streak_best_frame['class_name']}")

                # Reset alert status if no threats are detected for the duration of the cooldown period
                if alert_active and last_detection_time and current_time - last_detection_time > cool_down_time:
                    alert_active = False
                    last_detection_time = None  # Reset last detection time
                    logging.info("Alert state reset due to inactivity.")

                # Check if the user pressed the 'q' key to quit
                if cv2.waitKey(1) & 0xFF == ord('q') and self.firebase_service.live_detection_active is False:
                    self.firebase_service.live_detection_active = False
                    self.firebase_service.live_detection_activated = False
                    break

            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            error_message = f"Error during live video analysis: {str(e)}"
            self.firebase_service.stop_live_detection()
            logging.error(error_message)
            self.firebase_service.log_error(error_message)



            
'''
# Load a pretrained YOLOv8n model
model = YOLO('yolov8n.pt')

# Single stream with batch-size 1 inference
source = 'rtsp://example.com/media.mp4'  # RTSP, RTMP, TCP or IP streaming address

# Multiple streams with batched inference (i.e. batch-size 8 for 8 streams)
source = 'path/to/list.streams'  # *.streams text file with one streaming address per row

# Run inference on the source
results = model(source, stream=True)  # generator of Results objects


'''
