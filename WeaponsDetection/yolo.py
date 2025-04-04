import logging
import time
import cv2
from ultralytics import YOLO
from PIL import Image

# Load the YOLO model
model = YOLO('/Users/wmryny/Desktop/לימודים/פרוייקט גמר/FinalProject/GuardianViewRest/WeaponsDetection/guardianViewV2.pt') 


def live_detection_with_stream(model):

    # Start capturing video from the webcam

    cap = cv2.VideoCapture(1)
    

    if not cap.isOpened():
        print("Error: Could not open video stream from webcam.")
        return
    while cap.isOpened():
        # Capture frame-by-frame
        ret, frame = cap.read()
        results = model.predict(source=frame,show=True,conf=0.4,max_det=4)
        # Check if the user pressed the 'q' key to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
    # When everything done, release the video capture object
    cap.release()
    
    
    
   

def video_analysis(video_path):
    # Analyze a pre-recorded video
    results = model.predict(source=video_path, show=True)  # Set show=True to display the video with detections
    for result in results:
        # Process each frame's results as needed
        print(result.boxes)  # Example: print bounding boxes

def photo_analysis(image_path):
    # Analyze a photo, accepts path, PIL image, or ndarray
    image = Image.open(image_path)  # Load image with PIL
    results = model.predict(source=image, save=True)  # Save=True to save the output image with detections
    # Process the results
    print(results.boxes.xyxy)  # Example: print bounding boxes


def live_video_analysis( source=1, show=True):
        try:
            logging.info("Starting live video analysis")
            confidenceThreshold = 0.6

            
            cap = cv2.VideoCapture(source)  

            if not cap.isOpened():
                error_message = "Error: Could not open video stream."
                logging.error(error_message)
                #self.firebase_service.log_error(error_message)
                return

            alert_active = False
            last_detection_time = None
            threat_persist_time = 0.5  # Minimum duration a threat must be detected before alerting
            cool_down_time = 5  # Minimum duration of no threat detection required to reset the alert state

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Perform prediction on the current frame
                results = model.predict(source=frame, conf=confidenceThreshold, show=show,stream=True)
                current_time = time.time()
                threat_detected = False
                
                for r in results:
                    xyxy = r.boxes.xyxy  # Bounding box coordinates
                    confs = r.boxes.conf  # Confidence scores
                    classes = r.boxes.cls  # Class indices
                    for conf, cls_idx in zip(confs, classes):
                        if conf >= confidenceThreshold and cls_idx in [0, 1]:  # Assuming 0 and 1 are the class indices for threats
                            threat_detected = True
                            class_name = model.names[int(cls_idx)]
                            logging.info(f"Detected {class_name} with confidence {conf}")

                            if not alert_active:
                                if last_detection_time is None:
                                    last_detection_time = current_time
                                elif current_time - last_detection_time >= threat_persist_time:
                                    # Threat has persisted for the required duration; trigger an alert
                                    print(
                                        {'result': r, 'frame_idx': current_time, 'conf': conf, 'class_name': class_name, 'boxes': xyxy},
                                        'live_video'
                                    )
                                    alert_active = True
                                    last_detection_time = current_time  # Update detection time after generating an alert
                                    logging.info(f"Alert triggered for {class_name}")

                if not threat_detected:
                    if alert_active and current_time - last_detection_time > cool_down_time:
                        # Reset alert status if no threats are detected for the duration of the cooldown period
                        alert_active = False
                        last_detection_time = None  # Reset last detection time
                        logging.info("Alert state reset due to inactivity.")

                # Check if the user pressed the 'q' key to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            error_message = f"Error during live video analysis: {str(e)}"
            logging.error(error_message)
            #self.firebase_service.log_error(error_message)


###################DEMO OF MODEL###############
# Call the function to analyze a photo
#photo_analysis('/Users/wmryny/Downloads/weapon1.jpg')

#video_analysis('/Users/wmryny/Downloads/pexels-cottonbro-8717592 (2160p).mp4')

live_video_analysis()