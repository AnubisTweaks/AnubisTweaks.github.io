#!/usr/bin/env python3
"""Windows-friendly replacement for repo.sh.

Builds Packages, Packages.bz2, Packages.gz, Packages.zst and Release
from the .deb files in ./debfiles, without needing Linux or WSL.

Run from the repo folder:  python repo.py
"""
import bz2
import gzip
import hashlib
import io
import os
import shutil
import sys
import tarfile

DEB_DIR = "debfiles"
OUT_FILES = ["Packages", "Packages.bz2", "Packages.gz", "Packages.zst", "Release"]


# ---------- zstd support (built into Python 3.14+, else needs `pip install zstandard`) ----------
def _zstd_backend():
    try:
        from compression import zstd  # Python 3.14+
        return ("stdlib", zstd)
    except ImportError:
        pass
    try:
        import zstandard
        return ("zstandard", zstandard)
    except ImportError:
        return (None, None)


ZSTD_KIND, ZSTD = _zstd_backend()


def zstd_compress(data, level=19):
    if ZSTD_KIND == "stdlib":
        return ZSTD.compress(data, level=level)
    return ZSTD.ZstdCompressor(level=level).compress(data)


def zstd_decompress(data):
    if ZSTD_KIND == "stdlib":
        return ZSTD.decompress(data)
    return ZSTD.ZstdDecompressor().decompressobj().decompress(data)


# ---------- reading the control file out of a .deb ----------
def read_ar_members(path):
    """Yield (name, bytes) for each member of an ar archive (.deb)."""
    with open(path, "rb") as f:
        if f.read(8) != b"!<arch>\n":
            raise ValueError("not a valid .deb (ar) file")
        while True:
            header = f.read(60)
            if len(header) < 60:
                break
            name = header[0:16].decode().strip().rstrip("/")
            size = int(header[48:58].decode().strip())
            data = f.read(size)
            if size % 2:
                f.read(1)  # ar pads members to an even size
            yield name, data


def open_control_tar(name, data):
    if name.endswith(".zst"):
        if ZSTD is None:
            raise RuntimeError(
                "this .deb uses zstd compression; install Python 3.14+ "
                "or run: pip install zstandard"
            )
        return tarfile.open(fileobj=io.BytesIO(zstd_decompress(data)))
    # handles .tar, .tar.gz, .tar.xz, .tar.bz2 (and .lzma via xz)
    return tarfile.open(fileobj=io.BytesIO(data))


def read_control(deb_path):
    for name, data in read_ar_members(deb_path):
        if name.startswith("control.tar"):
            with open_control_tar(name, data) as tar:
                for member in tar.getmembers():
                    if member.name.lstrip("./") == "control":
                        text = tar.extractfile(member).read().decode("utf-8")
                        text = text.replace("\r\n", "\n").strip("\n")
                        return text
    raise ValueError("no control file found")


def control_field(control, field):
    for line in control.split("\n"):
        if line.lower().startswith(field.lower() + ":"):
            return line.split(":", 1)[1].strip()
    return ""


# ---------- building the repo ----------
def file_hashes(data):
    return (
        hashlib.md5(data).hexdigest(),
        hashlib.sha1(data).hexdigest(),
        hashlib.sha256(data).hexdigest(),
    )


def build_packages():
    entries = []
    debs = sorted(f for f in os.listdir(DEB_DIR) if f.lower().endswith(".deb"))
    for fname in debs:
        path = os.path.join(DEB_DIR, fname)
        try:
            control = read_control(path)
        except Exception as e:
            print(f"  skipped {fname}: {e}")
            continue
        with open(path, "rb") as f:
            data = f.read()
        md5, sha1, sha256 = file_hashes(data)
        extra = (
            f"Filename: {DEB_DIR}/{fname}\n"
            f"Size: {len(data)}\n"
            f"MD5sum: {md5}\n"
            f"SHA1: {sha1}\n"
            f"SHA256: {sha256}"
        )
        key = (control_field(control, "Package"), control_field(control, "Version"))
        entries.append((key, control + "\n" + extra))
        print(f"  added {fname}")
    entries.sort(key=lambda e: e[0])
    return "".join(text + "\n\n" for _, text in entries)


def main():
    if not os.path.isdir(DEB_DIR):
        sys.exit(f"Folder '{DEB_DIR}' not found. Run this from your repo folder.")
    if not os.path.isfile("Base"):
        sys.exit("File 'Base' not found. Run this from your repo folder.")

    for name in OUT_FILES:
        if os.path.exists(name):
            os.remove(name)

    print("Scanning packages...")
    packages = build_packages().encode("utf-8")

    outputs = {
        "Packages": packages,
        "Packages.bz2": bz2.compress(packages, 9),
        "Packages.gz": gzip.compress(packages, 9),
    }
    if ZSTD is not None:
        outputs["Packages.zst"] = zstd_compress(packages, 19)
    else:
        print("  note: zstd not available, skipping Packages.zst "
              "(use Python 3.14+ or run: pip install zstandard)")

    for name, data in outputs.items():
        with open(name, "wb") as f:
            f.write(data)

    shutil.copyfile("Base", "Release")
    with open("Release", "rb") as f:
        base = f.read().replace(b"\r\n", b"\n")
    if base and not base.endswith(b"\n"):
        base += b"\n"

    md5_lines, sha256_lines = [], []
    for name, data in outputs.items():
        md5, _, sha256 = file_hashes(data)
        md5_lines.append(f" {md5} {len(data)} {name}")
        sha256_lines.append(f" {sha256} {len(data)} {name}")

    release = base.decode("utf-8")
    release += "MD5Sum:\n" + "\n".join(md5_lines) + "\n"
    release += "SHA256:\n" + "\n".join(sha256_lines) + "\n"
    with open("Release", "w", encoding="utf-8", newline="\n") as f:
        f.write(release)

    print("Done")


if __name__ == "__main__":
    main()
