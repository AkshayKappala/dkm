import numpy as np
import pywt
import cv2
from dkm.shared.crypto_utils import derive_key

class DWTReconstructor:
    def __init__(self):
        self.wavelet = 'haar'  # You can choose other wavelets as needed

    def reconstruct_image(self, fragments, key):
        """
        Reconstruct the image from the provided fragments.

        Args:
            fragments: A dictionary containing the decrypted image fragments.
            key: The AES key used for decryption.

        Returns:
            Reconstructed image as a numpy array.
        """
        # Combine the fragments to reconstruct the image
        coeffs = [fragments['ll2'], fragments['lh2_hl2_hh2'], fragments['lh_hl_hh']]
        reconstructed_image = pywt.waverec2(coeffs, self.wavelet)

        return np.clip(reconstructed_image, 0, 255).astype(np.uint8)

    def save_reconstructed_image(self, image, output_path):
        """
        Save the reconstructed image to the specified path.

        Args:
            image: The reconstructed image as a numpy array.
            output_path: The path where the image will be saved.
        """
        cv2.imwrite(output_path, image)

# Add a standalone function for convenience
def reconstruct_image(fragments, key):
    reconstructor = DWTReconstructor()
    return reconstructor.reconstruct_image(fragments, key)