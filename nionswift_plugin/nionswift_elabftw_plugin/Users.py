import os
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

from nion.ui import Dialog

class Users():
    settings_dir = "~/ElabFTW Nionswift Plugin"

    def __init__(self):
        self.username = ""
        self.password = ""
        self.api_key = ""
        self.logged_in = False
        self.users = []

    def key_from_password(self, password, salt: bytes=None):
        if(salt == None):
            salt = secrets.token_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(str.encode(password))
        return key,salt

    def create_user(self):
        key,salt = self.key_from_password(self.password)
        nonce = secrets.token_hex(12)
        cipher = AESGCM(key).encrypt(bytes.fromhex(nonce), self.api_key.encode('utf-8'), None)
        try:
            f = open(os.path.expanduser(self.settings_dir)+'/users.txt', 'a+')
            f.write(self.username+':'+cipher.hex()+':'+nonce+':'+salt.hex()+'\n') # save cipher in hex string
            f.close()
        except OSError as ex:
            print(ex.strerror)
        except Exception as ex:
            print("Error creating user.")
            print(ex.strerror)

    def get_cipher(self, user):
        try:
            f = open(os.path.expanduser(self.settings_dir)+'/users.txt', 'r')
            for line in f:
                username,cipher,nonce,salt = tuple(line.rstrip('\n').split(':'))
                if user == username:
                    f.close()
                    return cipher,nonce,salt
            f.close()
            raise Exception("User not found.")
        except Exception as ex:
            print("Error reading user file.")
            print(ex.strerror)

    def login(self, user, password):
        cipher, nonce, salt = self.get_cipher(user)
        # Generate key from password
        key,salt = self.key_from_password(password, bytes.fromhex(salt))

        try:
            self.api_key = AESGCM(key).decrypt(bytes.fromhex(nonce),bytes.fromhex(cipher), None).decode('utf-8') # convert from hex string back to bytes
        except InvalidTag as ex:
            self.logged_in = False
            return False
        self.logged_in = True
        return True

    def logout(self):
        self.api_key = ""
        self.logged_in = False

    def get_users_list(self):
        self.users = []
        try:
            f = open(os.path.expanduser(self.settings_dir)+'/users.txt', 'r+')
            for line in f:
                self.users.append(line[:line.find(':')])
            f.close()
        except:
            self.users.append("<No User>")
        return self.users if len(self.users)>0 else ["<No User>"]
