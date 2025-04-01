# Image Transfer Project

## Overview
This project implements a secure image transfer system using AES-256 encryption and 2D Discrete Wavelet Transform (DWT) for image processing. The client application processes images, encrypts them, and sends the encrypted fragments to the server, which reconstructs the images from the received fragments.

## Project Structure
```
dkm
├── client
│   ├── client.py
│   ├── encryption
│   │   ├── aes_encryption.py
│   │   └── dwt_processor.py
│   └── utils
│       └── file_utils.py
├── server
│   ├── server.py
│   ├── decryption
│   │   ├── aes_decryption.py
│   │   └── dwt_reconstructor.py
│   └── utils
│       └── file_utils.py
├── shared
│   ├── crypto_utils.py
│   └── key_rotation_manager.py
├── requirements.txt
└── README.md
```

## Setup Instructions
1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Install the required dependencies listed in `requirements.txt` using pip:
   ```
   pip install -r requirements.txt
   ```

## Usage
### Client
- Run the client application using:
  ```
  python client/client.py
  ```
- The client will connect to the server, process the images in the `sent` directory, and send the encrypted fragments.

### Server
- Start the server application using:
  ```
  python server/server.py
  ```
- The server will listen for incoming connections and reconstruct the images from the received fragments.

## Encryption and Image Processing
- **AES-256 Encryption**: The project uses AES-256 for encrypting image fragments. The encryption key is derived from a SHA-256 hash of a user-defined password.
- **2D Discrete Wavelet Transform (DWT)**: Images are processed using DWT to decompose them into different frequency components. The relevant fragments (ll2, lh2, hl2, hh2, lh, hl, hh) are extracted and encrypted before transmission.

## Dependencies
- The project requires the following libraries:
  - `numpy`
  - `opencv-python`
  - `pycryptodome`
  - `scikit-image`

## Conclusion
This project demonstrates a secure method for transferring images over a network, utilizing advanced encryption techniques and image processing methods to ensure data integrity and confidentiality.