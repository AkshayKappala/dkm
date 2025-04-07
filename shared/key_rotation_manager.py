import os
import numpy as np
from skimage import io
from ID_MSE import compare_images
from kyber_py.ml_kem import ML_KEM_1024  # Import ML-KEM 1024 for key encapsulation

class KeyRotationManager:
    def __init__(self, similarity_threshold=0.85):
        """
        Initialize the key rotation manager.
        
        Args:
            similarity_threshold: Threshold below which we trigger key rotation (default: 0.85)
        """
        self.similarity_threshold = similarity_threshold
        self.last_image_path = None
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
        self.kem = ML_KEM_1024()  # Initialize ML-KEM 1024 for key encapsulation
    
    def is_image_file(self, filename):
        """Check if a file is an image based on its extension."""
        return any(filename.lower().endswith(ext) for ext in self.image_extensions)
    
    def should_rotate_key(self, file_path):
        """
        Determine if we should rotate keys based on image similarity.
        
        Args:
            file_path: Path to the current file
            
        Returns:
            tuple: (should_rotate, similarity_score or None, reason, new_password or None)
        """
        filename = os.path.basename(file_path)
        
        # Check if the file is an image
        if not self.is_image_file(filename):
            return False, None, "Not an image file", None
        
        # If no previous image to compare with
        if self.last_image_path is None:
            self.last_image_path = file_path
            return False, None, "First image received, no comparison possible", None
        
        try:
            # Load images
            prev_image = io.imread(self.last_image_path)
            current_image = io.imread(file_path)
            
            # Compare images
            similarity_score = compare_images(prev_image, current_image)
            
            # Update last image path for next comparison
            self.last_image_path = file_path
            
            # Determine if key rotation is needed
            if similarity_score < self.similarity_threshold:
                # Generate a new password using ML-KEM
                ek, dk = self.kem.keygen()  # Generate keypair (ek, dk)
                shared_key, ciphertext = self.kem.encaps(ek)  # Encapsulate shared key
                new_password = shared_key.hex()  # Use the shared key as the new password
                return True, similarity_score, f"Low similarity detected ({similarity_score:.4f} < {self.similarity_threshold})", new_password
            else:
                return False, similarity_score, f"Sufficient similarity ({similarity_score:.4f} >= {self.similarity_threshold})", None
                
        except Exception as e:
            self.last_image_path = file_path  # Update last image path
            return False, None, f"Error comparing images: {str(e)}", None