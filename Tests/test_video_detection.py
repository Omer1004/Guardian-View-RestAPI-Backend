import unittest
import cv2
import numpy as np
import os
import sys
from pathlib import Path
from ultralytics import YOLO

# Add the root directory to Python path to import from parent directory
sys.path.append(str(Path(__file__).parent.parent))

from Services.VideoProcessingService import VideoProcessingService

class TestVideoDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test resources that can be reused across test methods"""
        cls.test_videos_dir = os.path.join(os.path.dirname(__file__), "Test Videos")
        cls.video_processor = VideoProcessingService(None)  # Pass None instead of FirebaseService
        
        # Ensure test directory exists
        if not os.path.exists(cls.test_videos_dir):
            os.makedirs(cls.test_videos_dir)

    def setUp(self):
        """Set up resources for each test method"""
        self.test_frame = np.zeros((480, 640, 3), dtype=np.uint8)  # Create blank test frame

    def test_service_initialization(self):
        """Test if the video processing service initializes correctly"""
        self.assertIsNotNone(self.video_processor)
        self.assertIsNotNone(self.video_processor.model)
        self.assertIsNotNone(self.video_processor.modelLive)
        self.assertEqual(self.video_processor.confidenceThreshold, 0.6)
        self.assertEqual(self.video_processor.model_names, ['gun', 'knife', 'person'])

    def test_bbox_validation(self):
        """Test bounding box validation logic"""
        # Test valid bounding box (smaller than 5/6 of image)
        img_shape = (480, 640, 3)
        valid_bbox = np.array([100, 100, 400, 300])  # [x1, y1, x2, y2]
        self.assertTrue(self.video_processor.is_valid_bbox(valid_bbox, img_shape))

        # Test invalid bounding box (larger than 5/6 of image)
        invalid_bbox = np.array([0, 0, 639, 479])  # Almost full image
        self.assertFalse(self.video_processor.is_valid_bbox(invalid_bbox, img_shape))

    def test_severity_determination(self):
        """Test threat severity determination logic"""
        # Test different confidence levels
        self.assertEqual(self.video_processor.determine_severity(0.95, "knife"), "Emergency")
        self.assertEqual(self.video_processor.determine_severity(0.80, "knife"), "High")
        self.assertEqual(self.video_processor.determine_severity(0.70, "knife"), "Medium")
        self.assertEqual(self.video_processor.determine_severity(0.50, "knife"), "Low")
        
        # Test gun class severity elevation
        self.assertEqual(self.video_processor.determine_severity(0.50, "gun"), "Medium")  # Low -> Medium
        self.assertEqual(self.video_processor.determine_severity(0.70, "gun"), "High")    # Medium -> High
        self.assertEqual(self.video_processor.determine_severity(0.80, "gun"), "Emergency")  # High -> Emergency

    def test_video_analysis(self):
        """Test video analysis functionality"""
        # Create a test video with a simple pattern
        test_video_path = os.path.join(self.test_videos_dir, "test_video.mp4")
        self._create_test_video(test_video_path)

        try:
            # Test regular video analysis
            self.video_processor.video_analysis(test_video_path, showAnalysis=False)
            
            # Test longest streak analysis
            self.video_processor.video_analysis_longest_streak(test_video_path, showAnalysis=False)
            
            test_passed = True
        except Exception as e:
            test_passed = False
            print(f"Error in video processing: {str(e)}")

        self.assertTrue(test_passed)

    def _create_test_video(self, filepath):
        """Helper method to create a test video file with a pattern that might trigger detection"""
        height, width = 480, 640
        fps = 30
        seconds = 2

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

        # Create frames with a gun-like pattern
        for i in range(fps * seconds):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Draw a simple gun-like shape
            if i % 2 == 0:  # Alternate frames to test consistent detection
                cv2.rectangle(frame, (200, 200), (400, 250), (255, 255, 255), -1)  # "barrel"
                cv2.rectangle(frame, (350, 250), (400, 350), (255, 255, 255), -1)  # "handle"
            
            out.write(frame)

        out.release()

    def test_stop_live_detection(self):
        """Test if live detection can be properly stopped"""
        self.video_processor.stop_live_video_analysis()
        self.assertTrue(self.video_processor.stop_event is None or self.video_processor.stop_event.is_set())

    def tearDown(self):
        """Clean up after each test method"""
        if self.video_processor.stop_event:
            self.video_processor.stop_live_video_analysis()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run"""
        # Clean up test video files
        for file in os.listdir(cls.test_videos_dir):
            if file.endswith(".mp4"):
                os.remove(os.path.join(cls.test_videos_dir, file))

if __name__ == '__main__':
    unittest.main() 