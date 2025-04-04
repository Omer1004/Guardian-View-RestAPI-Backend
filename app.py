from flask import Flask, request, jsonify
import os
import signal
from Services.FirebaseService import FirebaseService
from Services.VideoProcessingService import VideoProcessingService


#this is a setup for the flask server
#Currently not in use because we are using the main.py file and we dont need to restful api commands 
#but we can use it later for testing purposes and to run the program from the server


app = Flask(__name__)

# Initialize services
firebase_service = FirebaseService()
video_processing_service = VideoProcessingService(firebase_service)
firebase_service.setVideoProcessingService(video_processing_service)
#test video analysis
#video_processing_service.video_analysis('Tests/Test Videos/3392580409-preview.mp4')

@app.route('/run_test_video', methods=['POST'])
def run_test_video():
    content = request.json
    video_path = content.get('video_path')
    if video_path:
        video_processing_service.video_analysis(video_path)
        return jsonify({"status": f"Analysis started for video {video_path}"})
    else:
        return jsonify({"error": "No video path provided"}), 400

@app.route('/run_live_video', methods=['POST'])
def run_live_video():
    source = request.json.get('source', 1)  # Default to 1 if not provided (Mac os webcam source) (0 for Windows)
    video_processing_service.live_video_analysis(source)
    return jsonify({"status": "Live video analysis started"})

@app.route('/stop', methods=['POST'])
def stop_processing():
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({"status": "Program stopped"})


@app.route('/get_alerts', methods=['GET'])
def get_alerts():
    #TODO: implement
    pass


#TODO: check this methud
@app.route('/analyze_video', methods=['POST'])
def analyze_video():
    content = request.json
    video_path = content.get('URL')
    if video_path:
        video_processing_service.video_analysis(video_path)
        return jsonify({"status": f"Analysis started for video {video_path}"})
    else:
        return jsonify({"error": "No video path provided"}), 400




if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
