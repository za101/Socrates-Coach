from cryptography.fernet import Fernet
import pyodbc

# Generate a key for encryption (Keep this key secure, as it's needed for decryption)
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Encrypt function
def encrypt_text(text):
    encrypted_text = cipher_suite.encrypt(text.encode())
    return encrypted_text

# Decrypt function
def decrypt_text(encrypted_text):
    decrypted_text = cipher_suite.decrypt(encrypted_text).decode()
    return decrypted_text

# Example data to be stored
plain_text = "This is a secret message."

# Encrypt the text before storing in the database
encrypted_text = encrypt_text(plain_text)

bin_text = pyodbc.Binary(encrypted_text)

# Decrypt the text when retrieving from the database
retrieved_text = decrypt_text(encrypted_text)

# Print the results
print("Original text:", plain_text)
print("Encrypted text:", encrypted_text)
print("Bin Encrypted text:", bin_text)
print("Decrypted text:", retrieved_text)

