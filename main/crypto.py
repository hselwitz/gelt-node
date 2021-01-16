import json
from codecs import encode

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key


def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(r"main/private_key.pem", "wb") as f:
        f.write(pem_private)

    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(r"main/public_key.pem", "wb") as f:
        f.write(pem_public)


def read_public_key():
    with open(r"main/public_key.pem", "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read(), backend=default_backend())
        return public_key


def read_private_key():
    with open(r"main/private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(), password=None, backend=default_backend()
        )
    return private_key


def serialize_public_key(key):
    return key.public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def serialized_key_to_str(key: bytes) -> str:
    key = repr(key)
    key = key[29:-29]
    return key


def deserialize_str_key(key: str):
    start = "-----BEGIN PUBLIC KEY-----\\"
    end = "\n-----END PUBLIC KEY-----\n"

    reconstructed_key = start + key + end
    reconstructed_key = encode(
        reconstructed_key.encode().decode("unicode_escape"), "raw_unicode_escape",
    )

    parameters = load_pem_public_key(reconstructed_key)

    return parameters


def key_to_str(key) -> str:
    key = serialize_public_key(key)
    key = serialized_key_to_str(key)

    return key


def bytes_sig_to_str(sig):
    return repr(sig[:])


def str_sig_to_byes(sig):
    return encode(sig.encode().decode("unicode_escape")[2:-1], "raw_unicode_escape")


def sign(private_key, message: dict):
    message = json.dumps(message).encode("utf-8")
    signature = private_key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH,),
        hashes.SHA256(),
    )

    return signature


def verify(public_key, signature: str, message: dict):
    message = json.dumps(message).encode("utf-8")
    verified = public_key.verify(
        signature,
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH,),
        hashes.SHA256(),
    )

    return verified
