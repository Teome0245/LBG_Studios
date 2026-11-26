"""extract_edge_cookies.py — Déverrouillage Windows & extraction des cookies Edge.

Utilise CreateFileW avec FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE
pour lire la base de données même quand Microsoft Edge est actif.
"""

from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sqlite3
import sys

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080
INVALID_HANDLE_VALUE = -1


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def copy_locked_file(src_path: str, dst_path: str) -> bool:
    """Copie un fichier verrouillé par un processus actif via l'API Windows CreateFileW partagée."""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateFileW(
        src_path,
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == INVALID_HANDLE_VALUE or handle == 0:
        return False

    buffer_size = 64 * 1024
    buf = ctypes.create_string_buffer(buffer_size)
    bytes_read = wintypes.DWORD(0)

    try:
        with open(dst_path, "wb") as f_out:
            while True:
                success = kernel32.ReadFile(handle, buf, buffer_size, ctypes.byref(bytes_read), None)
                if not success or bytes_read.value == 0:
                    break
                f_out.write(buf.raw[: bytes_read.value])
        return True
    finally:
        kernel32.CloseHandle(handle)


def dpapi_decrypt(encrypted_bytes: bytes) -> bytes:
    blob_in = DATA_BLOB(len(encrypted_bytes), ctypes.cast(ctypes.create_string_buffer(encrypted_bytes), ctypes.POINTER(ctypes.c_byte)))
    blob_out = DATA_BLOB()
    if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        addr = ctypes.cast(blob_out.pbData, ctypes.c_void_p).value
        raw = (ctypes.c_byte * blob_out.cbData).from_address(addr)
        decrypted = bytes(raw)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return decrypted
    raise RuntimeError("CryptUnprotectData failed")


def main() -> None:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    local_app_data = Path(os.environ.get("LOCALAPPDATA", r"C:\Users\sdesh\AppData\Local"))
    edge_dir = local_app_data / "Microsoft" / "Edge" / "User Data"

    local_state_path = edge_dir / "Local State"
    if not local_state_path.exists():
        print(json.dumps({"error": "Local State not found"}))
        return

    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    master_key = dpapi_decrypt(encrypted_key[5:])
    aesgcm = AESGCM(master_key)

    targets = {
        "deviantart": "%deviantart.com%",
        "pinterest": "%pinterest.com%",
        "tiktok": "%tiktok.com%",
    }

    results = {}
    saved = {}
    header = "# Netscape HTTP Cookie File\n# http://curl.haxx.se/rfc/cookie_spec.html\n\n"

    for prof in ["Default", "Profile 1"]:
        c_path = edge_dir / prof / "Network" / "Cookies"
        if not c_path.exists():
            c_path = edge_dir / prof / "Cookies"
        if not c_path.exists():
            continue

        tmp_db = Path(rf"C:\Agent_IA\edge_{prof}_copy.sqlite")
        ok = copy_locked_file(str(c_path), str(tmp_db))
        if not ok:
            results[prof] = {"copy_ok": False}
            continue

        try:
            conn = sqlite3.connect(tmp_db)
            cur = conn.cursor()
            prof_results = {}

            for platform, pat in targets.items():
                cur.execute("SELECT host_key, path, is_secure, expires_utc, name, encrypted_value FROM cookies WHERE host_key LIKE ?", (pat,))
                rows = cur.fetchall()
                cookies_list = []
                for host, path_val, is_sec, exp_utc, name, enc_val in rows:
                    val = ""
                    if enc_val[:3] in (b"v10", b"v11"):
                        try:
                            nonce = enc_val[3:15]
                            ciphertext = enc_val[15:]
                            val = aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8", errors="ignore")
                        except Exception:
                            continue
                    flag = "TRUE" if host.startswith(".") else "FALSE"
                    sec = "TRUE" if is_sec else "FALSE"
                    exp_epoch = int((exp_utc / 1000000) - 11644473600) if exp_utc > 0 else 0
                    cookies_list.append(f"{host}\t{flag}\t{path_val}\t{sec}\t{exp_epoch}\t{name}\t{val}")

                prof_results[platform] = len(cookies_list)
                if cookies_list:
                    c_file = Path(rf"C:\Agent_IA\{platform}_cookies.txt")
                    content = header + "\n".join(cookies_list) + "\n"
                    c_file.write_text(content, encoding="utf-8")
                    mirror_file = Path(rf"A:\LBG_Studios\tools\studio_content_engine\{platform}_cookies.txt")
                    try:
                        mirror_file.write_text(content, encoding="utf-8")
                        saved[platform] = {"count": len(cookies_list), "file": str(c_file), "mirror": str(mirror_file)}
                    except Exception as e_m:
                        saved[platform] = {"count": len(cookies_list), "file": str(c_file), "mirror_error": str(e_m)}

            conn.close()
            results[prof] = {"copy_ok": True, "counts": prof_results}
        except Exception as e:
            results[prof] = {"copy_ok": True, "error": str(e)}
        finally:
            if tmp_db.exists():
                tmp_db.unlink(missing_ok=True)

    print(json.dumps({"status": "ok", "results": results, "saved": saved}, indent=2))


if __name__ == "__main__":
    main()
