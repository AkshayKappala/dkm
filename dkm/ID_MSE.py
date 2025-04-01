import numpy as np
from skimage import io, img_as_float
from skimage.transform import resize

def compute_mse(image1, image2):
    # Compute Mean Squared Error
    mse = np.mean((image1 - image2) ** 2)
    return mse

def compute_similarity(image1, image2):
    # Compute MSE
    mse = compute_mse(image1, image2)
    # Compute similarity score
    similarity = 1 - mse
    return similarity

def compare_images(image1, image2):
    # Convert images to float
    image1 = img_as_float(image1)
    image2 = img_as_float(image2)

    # Resize images to the same dimensions
    image2 = resize(image2, image1.shape)

    # Compute similarity
    similarity = compute_similarity(image1, image2)
    return similarity

if __name__ == "__main__":
    # Load images
    image1 = io.imread('images/1.jpg')
    image2 = io.imread('images/2.jpg')

    # Compare images using similarity score
    similarity_score = compare_images(image1, image2)
    print(f"Similarity Score: {similarity_score}")