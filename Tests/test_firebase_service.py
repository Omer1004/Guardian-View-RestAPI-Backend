import unittest
from unittest.mock import patch, MagicMock
from firebase_admin import auth
from Services.FirebaseService import FirebaseService  

class TestFirebaseService(unittest.TestCase):

    def setUp(self):
        # This method will be called before each test function
        self.firebase_service = FirebaseService()

    @patch('firebase_admin.auth.create_user')
    def test_create_user(self, mock_create_user):
        mock_user_record = MagicMock()
        mock_user_record.uid = "12345"
        mock_create_user.return_value = mock_user_record
        
        user = self.firebase_service.create_user("test@example.com", "password")
        self.assertEqual(user.uid, "12345")
        mock_create_user.assert_called_once_with(email="test@example.com", password="password")

    @patch('firebase_admin.auth.delete_user')
    def test_delete_user(self, mock_delete_user):
        # Mock the delete_user method
        mock_delete_user.return_value = None
        
        # Call the method
        result = self.firebase_service.delete_user("12345")
        
        # Check that the method was called correctly
        self.assertTrue(result)
        mock_delete_user.assert_called_once_with("12345")

    
    # Test the upload_frame metho§
    #TODO: not working yet need to fix it 
    
    @patch('firebase_admin.storage.bucket')
    def test_upload_frame(self, mock_blob):
        # Mock the bucket method
        mock_blob.return_value = MagicMock()
        
        # Call the method
        result = self.firebase_service.upload_frame("Results/knife_1711058730.115149_2024-03-22_00-05-31.jpg", "knife_1711058730.115149_2024-03-22_00-05-31.jpg")
        
        # Check that the method was called correctly
        self.assertIsNotNone(result)
        mock_blob.assert_called_once_with()
        mock_blob.return_value.blob.assert_called_once_with("knife_1711058730.115149_2024-03-22_00-05-31.jpg")

        

if __name__ == '__main__':
    unittest.main()


#python3 -m unittest Tests.test_firebase_service.py
