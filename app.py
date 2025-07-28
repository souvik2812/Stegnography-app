from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image
import numpy as np
import cv2
import io
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.backends import default_backend
import os

app = Flask(__name__)

def encrypt_message(message, key):
    padder = padding.PKCS7(128).padder()
    padded_message = padder.update(message.encode()) + padder.finalize()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_message = encryptor.update(padded_message) + encryptor.finalize()
    return iv + encrypted_message

def decrypt_message(encrypted_message, key):
    iv = encrypted_message[:16]
    encrypted_message = encrypted_message[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_message = decryptor.update(encrypted_message) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    message = unpadder.update(decrypted_message) + unpadder.finalize()
    return message.decode()

def encode_message(image, message, key):
    encrypted_message = encrypt_message(message, key)
    binary_message = ''.join(format(byte, '08b') for byte in encrypted_message) + '00000000'
    data = np.array(image)
    
    if len(binary_message) > data.size:
        raise ValueError("Message too long to hide in this image.")
    
    index = 0
    for value in np.nditer(data, op_flags=['readwrite']):
        if index < len(binary_message):
            value[...] = (value & 0xFE) | int(binary_message[index])
            index += 1
    
    return Image.fromarray(data)

def decode_message(image, key):
    data = np.array(image)
    binary_message = ""
    
    for value in np.nditer(data):
        binary_message += str(value & 1)
        if binary_message.endswith("00000000"):
            break
    
    if not binary_message.endswith("00000000"):
        return None
    
    encrypted_message = bytes(int(binary_message[i:i + 8], 2) for i in range(0, len(binary_message) - 8, 8))
    try:
        return decrypt_message(encrypted_message, key)
    except ValueError:
        return "Wrong password or image is not encoded"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    file = request.files['imageInput']
    message = request.form['messageInput']
    password = request.form['passwordInput']
    
    if not file or not message or not password:
        return "Please provide an image, a message, and a password.", 400
    
    key = hashes.Hash(hashes.SHA256(), backend=default_backend())
    key.update(password.encode())
    key = key.finalize()
    
    image = Image.open(file)
    encoded_image = encode_message(image.convert("RGB"), message, key)
    
    img_byte_arr = io.BytesIO()
    encoded_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return send_file(img_byte_arr, mimetype='image/png', as_attachment=True, download_name='hidden_data_image.png')

@app.route('/decode', methods=['POST'])
def decode():
    file = request.files['encodedImageInput']
    password = request.form['passwordInput']
    
    if not file or not password:
        return "Please provide an encoded image and a password.", 400
    
    key = hashes.Hash(hashes.SHA256(), backend=default_backend())
    key.update(password.encode())
    key = key.finalize()
    
    image = Image.open(file)
    message = decode_message(image.convert("RGB"), key)
    
    if message is None:
        return jsonify({"message": "Image is not encoded"})
    elif message == "Wrong password or image is not encoded":
        return jsonify({"message": "Wrong password or image is not encoded"})
    
    return jsonify({"decodedMessage": message})

if __name__ == '__main__':
    app.run(debug=True)
