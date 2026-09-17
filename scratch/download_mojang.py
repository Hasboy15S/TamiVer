import pathlib
import hashlib
import time
import httpx

url = "https://piston-data.mojang.com/v1/objects/4707d00eb834b446575d89a61a11b5d548d8c001/server.jar"
dest = pathlib.Path("data/server/cache/mojang_1.21.4.jar")
dest.parent.mkdir(parents=True, exist_ok=True)
expected_hash = "1066970b09e9c671844572291c4a871cc1ac2b85838bf7004fa0e778e10f1358"

print("Starting robust download of mojang_1.21.4.jar...")

while True:
    current_size = dest.stat().st_size if dest.exists() else 0
    headers = {}
    if current_size > 0:
        headers["Range"] = f"bytes={current_size}-"
        print(f"Resuming download from byte {current_size}...")

    try:
        with httpx.stream("GET", url, headers=headers, timeout=30.0, follow_redirects=True) as resp:
            if resp.status_code in (200, 206):
                mode = "ab" if resp.status_code == 206 else "wb"
                with open(dest, mode) as f:
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        f.write(chunk)
                        print(f"Downloaded: {dest.stat().st_size} bytes", end="\r")
    except Exception as e:
        print(f"\nConnection interrupted ({e}). Retrying in 2s...")
        time.sleep(2)
        continue

    # Verify sha256
    data = dest.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    print(f"\nDownloaded total: {len(data)} bytes. Hash: {h}")
    if h == expected_hash:
        print("SUCCESS: Hash matched perfectly!")
        break
    else:
        print("Hash mismatch! Redownloading from scratch...")
        dest.unlink(missing_ok=True)
