import asyncio
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import os
from Crypto.Util.Padding import pad as crypto_pad
from functools import partial
from cor_lab.config.config import settings


def pad(data: bytes, block_size: int) -> bytes:
    """
    Эта функция добавляет необходимое количество байтов к данным, чтобы они соответствовали размеру блока. Если данные являются строкой, они сначала кодируются в байты.
    Параметры:
    data: данные для дополнения (в байтах).
    block_size: размер блока, к которому нужно дополнить данные.
    Возвращает: дополненные данные.
    """
    if isinstance(data, str):
        data = data.encode()
    return crypto_pad(data, block_size)


async def encrypt_data(data: bytes, key: bytes) -> bytes:
    """
    Эта асинхронная функция шифрует данные с использованием AES в режиме CBC.

    Параметры:
    data: данные для шифрования (в байтах).
    key: ключ шифрования (в байтах).
    Процесс:
    Генерируется вектор инициализации (IV).
    Данные шифруются.
    IV и зашифрованные данные кодируются в Base64 и возвращаются.
    """

    cipher = AES.new(key, AES.MODE_CBC)
    encrypted_data = cipher.encrypt(pad(data, AES.block_size))
    encoded_data = base64.b64encode(cipher.iv + encrypted_data)
    return encoded_data


def _sync_decrypt_data_impl(encrypted_data: bytes, key: bytes) -> str:
    if len(key) not in [16, 24, 32]:
        raise ValueError("Key must be 16, 24, or 32 bytes long.")

    decoded_data = base64.b64decode(encrypted_data)
    iv = decoded_data[: AES.block_size]
    ciphertext = decoded_data[AES.block_size :]

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return decrypted_data.decode("utf-8")


async def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    """
    Эта асинхронная функция дешифрует данные, зашифрованные функцией encrypt_data.
    CPU-интенсивные части выполняются в отдельном потоке.
    """
    try:
        result = await asyncio.to_thread(_sync_decrypt_data_impl, encrypted_data, key)
        return result
    except (ValueError, KeyError) as e:

        raise ValueError("Decryption failed. Invalid key or corrupted data.") from e


async def generate_aes_key(key_size: int = 16) -> bytes:
    """
    Генерирует новый ключ для AES.
    """
    if key_size not in [16, 24, 32]:
        raise ValueError("Key size must be 16, 24, or 32 bytes.")
    return secrets.token_bytes(key_size)


async def generate_recovery_code() -> str:
    """
    Генерирует код восстановления.
    """
    return secrets.token_urlsafe(64)


async def encrypt_user_key(key: bytes) -> str:
    """
    Шифрует пользовательский ключ.
    """
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )
    aes_key = await asyncio.to_thread(kdf.derive, settings.aes_key.encode())

    cipher = Fernet(base64.urlsafe_b64encode(aes_key))
    encrypted_key = cipher.encrypt(key)
    return base64.urlsafe_b64encode(salt + encrypted_key).decode()


def _sync_decrypt_user_key_impl(encrypted_key: str, aes_key_setting: str) -> bytes:
    encrypted_data = base64.urlsafe_b64decode(encrypted_key)
    salt = encrypted_data[:16]
    ciphertext = encrypted_data[16:]

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )
    aes_key_derived = kdf.derive(aes_key_setting.encode())

    cipher = Fernet(base64.urlsafe_b64encode(aes_key_derived))
    return cipher.decrypt(ciphertext)


async def decrypt_user_key(encrypted_key: str) -> bytes:
    """
    Дешифрует зашифрованный пользовательский ключ.
    CPU-интенсивные части выполняются в отдельном потоке.
    """
    try:
        result = await asyncio.to_thread(
            partial(_sync_decrypt_user_key_impl, encrypted_key, settings.aes_key)
        )
        return result
    except Exception as e:
        raise ValueError("Decryption failed. Invalid key or corrupted data.") from e
