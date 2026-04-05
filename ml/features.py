"""
features.py
-----------
Extracts the 18-feature vector that the trained ensemble model expects.

Feature order (must never change — model was trained on this):
  0  laplacian_var      — overall sharpness (Laplacian variance)
  1  center_sharpness   — sharpness in the centre crop (subject area)
  2  sobel_var          — edge sharpness (Sobel gradient mean)
  3  fft_mean           — high-frequency energy via FFT (detail/blur proxy)
  4  brightness         — mean brightness (HSV value channel)
  5  brightness_std     — brightness spread (exposure evenness)
  6  is_too_dark        — hard flag: brightness < 60
  7  is_too_bright      — hard flag: brightness > 220
  8  contrast           — greyscale standard deviation
  9  noise              — Gaussian-blur residual (grain estimate)
  10 saturation         — mean HSV saturation
  11 l_mean             — LAB lightness channel mean
  12 a_mean             — LAB green-red channel mean
  13 b_mean             — LAB blue-yellow channel mean
  14 entropy            — histogram entropy (tonal distribution)
  15 blown              — % pixels above 250 (blown highlights)
  16 crushed            — % pixels below 5 (crushed shadows)
  17 local_contrast     — local detail quality (high-pass RMS)

All images are resized to 224x224 before extraction (same as training).
Rotation is automatically corrected via EXIF and dimension check.
"""

import cv2
import numpy as np
from PIL import Image
import PIL.ExifTags


def read_image_corrected(image_path: str):
    """
    Load image and fix rotation via EXIF metadata.
    Falls back to dimension-based fix if no EXIF.
    Returns BGR numpy array or None.
    """
    try:
        pil_img = Image.open(image_path)
        try:
            exif = pil_img._getexif()
            if exif:
                for tag, value in exif.items():
                    if PIL.ExifTags.TAGS.get(tag) == 'Orientation':
                        if value == 3:
                            pil_img = pil_img.rotate(180, expand=True)
                        elif value == 6:
                            pil_img = pil_img.rotate(270, expand=True)
                        elif value == 8:
                            pil_img = pil_img.rotate(90, expand=True)
                        break
        except Exception:
            pass
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception:
        img = cv2.imread(image_path)

    if img is None:
        return None

    # Dimension-based fix (catches manipulated photos that lost EXIF)
    h, w = img.shape[:2]
    if w > h:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    return img


def extract_features(image_path: str) -> list:
    """
    Load image from path and return an 18-element list of floats.
    Raises ValueError if the image cannot be read.
    """
    img = read_image_corrected(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    img  = cv2.resize(img, (224, 224))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab  = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    # 0 - Overall Laplacian sharpness
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # 1 - Centre-crop sharpness
    h, w = gray.shape
    center = gray[h // 4: 3 * h // 4, w // 4: 3 * w // 4]
    center_sharpness = float(cv2.Laplacian(center, cv2.CV_64F).var())

    # 2 - Sobel edge sharpness
    sobelx   = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely   = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    sobel_var = float(np.hypot(sobelx, sobely).mean())

    # 3 - FFT high-frequency mean
    fft      = np.fft.fftshift(np.fft.fft2(gray))
    fft_mean = float(np.mean(20 * np.log(np.abs(fft) + 1)))

    # 4 & 5 - Brightness mean + std
    brightness     = float(np.mean(hsv[:, :, 2]))
    brightness_std = float(np.std(hsv[:, :, 2]))

    # 6 & 7 - Hard exposure flags
    is_too_dark   = 1.0 if brightness < 60  else 0.0
    is_too_bright = 1.0 if brightness > 220 else 0.0

    # 8 - Contrast
    contrast = float(gray.std())

    # 9 - Noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    noise   = float(np.mean(np.abs(gray.astype(float) - blurred.astype(float))))

    # 10 - Saturation
    saturation = float(np.mean(hsv[:, :, 1]))

    # 11, 12, 13 - LAB channels
    l_mean = float(np.mean(lab[:, :, 0]))
    a_mean = float(np.mean(lab[:, :, 1]))
    b_mean = float(np.mean(lab[:, :, 2]))

    # 14 - Histogram entropy
    hist      = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    hist_norm = hist / hist.sum()
    entropy   = float(-np.sum(hist_norm * np.log2(hist_norm + 1e-10)))

    # 15 - Blown highlights
    blown = float(np.sum(gray > 250) / gray.size)

    # 16 - Crushed shadows
    crushed = float(np.sum(gray < 5) / gray.size)

    # 17 - Local contrast (high-pass RMS)
    high_pass     = gray.astype(np.float32) - cv2.GaussianBlur(gray, (15, 15), 0)
    local_var     = cv2.GaussianBlur(high_pass ** 2, (15, 15), 0)
    local_contrast = float(np.sqrt(np.mean(local_var)))

    return [
        laplacian_var,
        center_sharpness,
        sobel_var,
        fft_mean,
        brightness,
        brightness_std,
        is_too_dark,
        is_too_bright,
        contrast,
        noise,
        saturation,
        l_mean,
        a_mean,
        b_mean,
        entropy,
        blown,
        crushed,
        local_contrast,
    ]
