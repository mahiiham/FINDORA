from pathlib import Path
from uuid import uuid4
from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'jfif', 'png', 'webp'}
ALLOWED_FORMATS = {'JPEG', 'MPO', 'PNG', 'WEBP'}   # MPO = multi-picture JPEG written by many phone cameras


def compute_phash(img):
    """Lightweight perceptual hash (difference hash, 8x8 -> 64 bits) computed with
    only PIL — no extra ML dependency required. Used by the AI matching engine to
    compare *visual* similarity of lost/found photos alongside the text/TF-IDF score."""
    try:
        small = img.convert('L').resize((9, 9), Image.LANCZOS)
        pixels = list(small.getdata())
        bits = []
        for row in range(8):
            for col in range(8):
                bits.append('1' if pixels[row * 9 + col] > pixels[row * 9 + col + 1] else '0')
        return format(int(''.join(bits), 2), '016x')
    except Exception:
        return None


def hamming_distance(a, b):
    if not a or not b or len(a) != len(b):
        return None
    try:
        return bin(int(a, 16) ^ int(b, 16)).count('1')
    except ValueError:
        return None


def image_similarity(a, b):
    """Returns a 0..1 visual-similarity score from two perceptual hashes, or None
    if either photo is missing. 64 total bits compared via Hamming distance."""
    d = hamming_distance(a, b)
    if d is None:
        return None
    return max(0.0, 1 - (d / 64.0))


def save_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None, None
    ext = file_storage.filename.rsplit('.', 1)[-1].lower() if '.' in file_storage.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError('Only JPEG, PNG and WEBP images are allowed.')
    try:
        img = Image.open(file_storage.stream)
        if img.format not in ALLOWED_FORMATS:
            raise ValueError('Invalid image format.')
        img.verify()
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream)
        img = ImageOps.exif_transpose(img).convert('RGB')   # honour the phone's rotation flag so photos are upright
        img.thumbnail((1400, 1400))
    except (UnidentifiedImageError, OSError):
        raise ValueError('Uploaded file is not a valid image.')
    name = f"{uuid4().hex}.jpg"
    folder = Path(current_app.config['UPLOAD_FOLDER'])
    folder.mkdir(parents=True, exist_ok=True)
    img.save(folder / name, 'JPEG', quality=88, optimize=True)
    thumb = img.copy(); thumb.thumbnail((480, 480)); thumb.save(folder / f"thumb_{name}", 'JPEG', quality=80, optimize=True)
    phash = compute_phash(img)
    return name, phash
