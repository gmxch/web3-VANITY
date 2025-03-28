import base58
import os
import nacl.signing
import multiprocessing

# Ganti sesuai kebutuhan
PREFIX = "GMXCH"
NUM_WORKERS = multiprocessing.cpu_count()  # Gunakan semua core CPU

def generate_solana_keypair():
    """Generate Solana keypair sampai menemukan yang sesuai prefix"""
    while True:
        private_key = os.urandom(32)
        signer = nacl.signing.SigningKey(private_key)
        public_key = signer.verify_key.encode()
        solana_address = base58.b58encode(public_key).decode()

        if solana_address.startswith(PREFIX):
            return solana_address, base58.b58encode(private_key).decode()

def worker(queue, stop_event):
    """Worker untuk mencari vanity address secara paralel"""
    while not stop_event.is_set():  # Hanya lanjut jika belum ada yang menemukan address
        address, private_key = generate_solana_keypair()
        if not queue.empty():  # Jika sudah ada hasil dari worker lain, stop
            break
        queue.put((address, private_key))
        stop_event.set()  # Set flag supaya worker lain berhenti
        break

if __name__ == "__main__":
    queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    processes = []

    # Mulai worker sesuai jumlah core CPU
    for _ in range(NUM_WORKERS):
        p = multiprocessing.Process(target=worker, args=(queue, stop_event))
        processes.append(p)
        p.start()

    # Ambil hasil pertama yang ditemukan
    address, private_key = queue.get()

    # Hentikan semua proses lain
    stop_event.set()
    for p in processes:
        p.terminate()
        p.join()

    # Simpan hasil
    with open("solana_address.txt", "w") as f:
    f.write(f"Address: {address}\n")
    f.write(f"Solexplorer: https://solscan.io/account/{address}\n")

    with open("solana_private.txt", "w") as f:
        f.write(f"Private Key: {private_key}\n")

    print(f"✅ Address ditemukan: {address}")
    print(f"🔒 Private Key tersimpan di artifact!")
