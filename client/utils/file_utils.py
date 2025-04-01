import os
from PIL import Image

def read_image(directory):
    """
    Reads all image files from the specified directory.

    Args:
        directory (str): Path to the directory containing image files.

    Returns:
        list: List of image filenames in the directory.
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    try:
        return [
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(tuple(image_extensions))
        ]
    except Exception as e:
        print(f"Error reading images from {directory}: {e}")
        return []

def write_image(image, file_path):
    """Write an image to the specified file path."""
    try:
        image.save(file_path)
        print(f"Image saved to {file_path}")
    except Exception as e:
        print(f"Error saving image {file_path}: {e}")

def get_file_extension(file_path):
    """Get the file extension of the specified file path."""
    return os.path.splitext(file_path)[1].lower()

def is_image_file(file_path):
    """Check if the file is an image based on its extension."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    return get_file_extension(file_path) in image_extensions

def create_directory(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Directory created: {directory}")
        else:
            print(f"Directory already exists: {directory}")
    except Exception as e:
        print(f"Error creating directory {directory}: {e}")