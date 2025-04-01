import numpy as np
import pywt
import cv2
from shared.crypto_utils import decrypt_aes

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
        # Decrypt the fragments
        ll2 = decrypt_aes(fragments['ll2'], key)
        lh2 = decrypt_aes(fragments['lh2'], key)
        hl2 = decrypt_aes(fragments['hl2'], key)
        hh2 = decrypt_aes(fragments['hh2'], key)

        # Combine the fragments to reconstruct the image
        coeffs = (ll2, (lh2, hl2, hh2))
        reconstructed_image = pywt.idwt2(coeffs, self.wavelet)

        return np.clip(reconstructed_image, 0, 255).astype(np.uint8)

    def save_reconstructed_image(self, image, output_path):
        """
        Save the reconstructed image to the specified path.

        Args:
            image: The reconstructed image as a numpy array.
            output_path: The path where the image will be saved.
        """
        cv2.imwrite(output_path, image)