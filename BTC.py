import os
import base58
import ecdsa
import hashlib
import multiprocessing

# Ganti sesuai kebutuhan
PREFIX = "1GMXCH"
NUM_WORKERS = multiprocessing.cpu_count()  # Gunakan semua core CPU

def generate_btc_keypair():
    """Generate Bitcoin keypair sampai menemukan yang sesuai prefix"""
    while True:
        # Generate Private Key (32 bytes)
        private_key = os.urandom(32)
        sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
        vk = sk.verifying_key

        # Generate Public Key (Compressed)
        public_key = b"\x02" + vk.to_string()[:32] if vk.to_string()[63] % 2 == 0 else b"\x03" + vk.to_string()[:32]

        # Hash Public Key (SHA256 + RIPEMD160)
        sha256_hash = hashlib.sha256(public_key).digest()
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
        btc_address_raw = b"\x00" + ripemd160_hash  # Prefix 0x00 untuk mainnet

        # Base58Check Encoding
        checksum = hashlib.sha256(hashlib.sha256(btc_address_raw).digest()).digest()[:4]
        btc_address = base58.b58encode(btc_address_raw + checksum).decode()

        if btc_address.startswith(PREFIX):
            return btc_address, base58.b58encode(private_key).decode()

def worker(queue, stop_event):
    """Worker untuk mencari vanity address secara paralel"""
    while not stop_event.is_set():
        address, private_key = generate_btc_keypair()
        if not queue.empty():
            break
        queue.put((address, private_key))
        stop_event.set()
        break

if __name__ == "__main__":
    queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    processes = []

    for _ in range(NUM_WORKERS):
        p = multiprocessing.Process(target=worker, args=(queue, stop_event))
        processes.append(p)
        p.start()

    address, private_key = queue.get()

    stop_event.set()
    for p in processes:
        p.terminate()
        p.join()

    # Simpan hasil
    with open("btc_address.txt", "w") as f:
        f.write(f"Address: {address}\n")
        f.write(f"Explorer: https://www.blockchain.com/btc/address/{address}\n")

    with open("btc_private.txt", "w") as f:
        f.write(f"BTC : {address}\n")
        f.write(f"KEY : {private_key}\n")

    print(f"✅ Address ditemukan: {address}")
    print(f"🔒 Private Key tersimpan di artifact!")
