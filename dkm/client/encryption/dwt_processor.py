import numpy as np
import pywt
from skimage import io

class DWTProcessor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = io.imread(image_path, as_gray=True)

    def decompose(self):
        coeffs2 = pywt.dwt2(self.image, 'haar')
        cA, (cH, cV, cD) = coeffs2
        return cA, cH, cV, cD

    def extract_fragments(self):
        cA, cH, cV, cD = self.decompose()
        ll2 = cA
        lh2 = cH
        hl2 = cV
        hh2 = cD
        return ll2, lh2, hl2, hh2

    def save_fragments(self, fragments, output_prefix):
        ll2, lh2, hl2, hh2 = fragments
        io.imsave(f"{output_prefix}_ll2.png", ll2)
        io.imsave(f"{output_prefix}_lh2.png", lh2)
        io.imsave(f"{output_prefix}_hl2.png", hl2)
        io.imsave(f"{output_prefix}_hh2.png", hh2)