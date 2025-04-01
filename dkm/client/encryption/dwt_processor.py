import numpy as np
import pywt
from skimage import io

class DWTProcessor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = io.imread(image_path, as_gray=True)

    def decompose(self):
        coeffs = pywt.wavedec2(self.image, 'haar', level=2)
        ll2, (lh2, hl2, hh2), (lh, hl, hh) = coeffs
        return ll2, (lh2, hl2, hh2), (lh, hl, hh)

    def extract_fragments(self):
        ll2, (lh2, hl2, hh2), (lh, hl, hh) = self.decompose()
        return ll2, lh2, hl2, hh2

    def save_fragments(self, fragments, output_prefix):
        ll2, lh2, hl2, hh2 = fragments
        io.imsave(f"{output_prefix}_ll2.png", ll2)
        io.imsave(f"{output_prefix}_lh2.png", lh2)
        io.imsave(f"{output_prefix}_hl2.png", hl2)
        io.imsave(f"{output_prefix}_hh2.png", hh2)

# Add a standalone function for convenience
def process_image(image_path):
    processor = DWTProcessor(image_path)
    return processor.decompose()