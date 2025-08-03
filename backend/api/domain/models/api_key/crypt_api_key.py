import os
import random
import string

from cryptography.fernet import Fernet
from pydantic import RootModel, StrictStr

AES_KEY = os.environ.get("AES_KEY")


class EncryptedApiKey(RootModel):
    root: StrictStr

    def decrypt(self) -> "DecryptedApiKey":
        if AES_KEY is None:
            raise ValueError("AES_KEY is not set")
        fernet = Fernet(AES_KEY.encode("utf-8"))
        return DecryptedApiKey(root=fernet.decrypt(self.root.encode("utf-8")).decode("utf-8"))


class DecryptedApiKey(RootModel):
    root: StrictStr

    def encrypt(self) -> EncryptedApiKey:
        if AES_KEY is None:
            raise ValueError("AES_KEY is not set")
        fernet = Fernet(AES_KEY.encode("utf-8"))
        return EncryptedApiKey(root=fernet.encrypt(self.root.encode("utf-8")).decode("utf-8"))


def create_encrypted_api_key() -> EncryptedApiKey:
    decrypted_api_key = "".join(random.choices(string.ascii_lowercase + string.digits, k=32))
    if AES_KEY is None:
        raise ValueError("AES_KEY is not set")
    fernet = Fernet(AES_KEY.encode("utf-8"))
    encrypted_api_key = fernet.encrypt(decrypted_api_key.encode("utf-8"))

    return EncryptedApiKey(root=encrypted_api_key.decode("utf-8"))
