from cryptography.fernet import Fernet

def generate_key():
    key = Fernet.generate_key()
    print(f"Generated Fernet key: {key.decode()}")
    return key

if __name__ == "__main__":
    generate_key()
