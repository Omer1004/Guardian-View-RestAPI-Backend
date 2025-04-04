import logging
import time
import cv2
import firebase_admin
from firebase_admin import credentials

from Services.FirebaseService  import FirebaseService
from Services.VideoProcessingService import VideoProcessingService
import os



def init_services():
    # Initialize services
    firebase_service = FirebaseService()
    video_processing_service = VideoProcessingService(firebase_service)
    firebase_service.setVideoProcessingService(video_processing_service)
    return video_processing_service, firebase_service

def proccess_test_videos(video_processing_service, firebase_service):
    # Get all video names in the test video folder
    test_video_path = "Tests/Test Videos/"
    test_video_names = [video_name for video_name in os.listdir(test_video_path) if video_name.endswith(".mp4")]

    # Process test videos
    for video_name in test_video_names:
        video_path = test_video_path + video_name
        video_processing_service.video_analysis(video_path,showAnalysis=True)
        logging.info(f"Video analysis completed for {video_name}")



# the live function is activated in main function because show analysis is only possible on the main thread
# otherwise it will run in the background and will not be able to show the analysis and we will use docker to run the application when we will have
# streams from the cameras
def main():
    
    video_processing_service, firebase_service = init_services()
    #proccess_test_videos(video_processing_service, firebase_service)
    live_activated = True
    try:
        # Keep the main thread alive to listen to Firestore updates
        while True:
            time.sleep(1)
            if firebase_service.live_detection_active and not live_activated:
                live_activated = True
                video_processing_service.live_video_analysis()
            elif not firebase_service.live_detection_active and live_activated:
                live_activated = False
                firebase_service.stop_live_detection()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        firebase_service.stop_live_detection()
    
    
    
def test_main():
    video_processing_service, firebase_service = init_services()
    #video_processing_service.live_video_analysis()
    #time.sleep(30)
    #firebase_service.stop_live_detection()
    proccess_test_videos(video_processing_service, firebase_service)
    


if __name__ == "__main__":
    main()

    
'''
docker build -t guardianview .


docker run guardianview

xhost +local:docker
docker run -it \
    --env DISPLAY=$DISPLAY \
    --env LIBGL_ALWAYS_INDIRECT=1 \
    --volume /tmp/.X11-unix:/tmp/.X11-unix \
    --volume path_to_local_directory:/app \
    guardianview

    CURRENTLY DOCKER DOESNT SUPPORT GUI APPLICATIONS AND IT IS NOT POSSIBLE TO RUN THE APPLICATION IN DOCKER
      BECAUSE THE APLICATION MAKES USAGE OF LOCAL COMPUTER RESOURCES SUCH AS CAMERA AND DISPLAY AND STORAGE

'''

