import os
from PIL import Image

def read_image(file_path):
    """Read an image from the specified file path."""
    try:
        with Image.open(file_path) as img:
            return img.convert('RGB')  # Convert to RGB if not already
    except Exception as e:
        print(f"Error reading image {file_path}: {e}")
        return None

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
    """Create a directory if it does not exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory created: {directory}")
    else:
        print(f"Directory already exists: {directory}")