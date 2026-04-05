"""
pipeline.py
-----------
Main entry point called by Django views after a photo is uploaded.

How it works:
  1. Extract 18 features from the image (sharpness, brightness, FFT, noise, etc.)
  2. Scale features with the trained StandardScaler
  3. Run the trained Ensemble classifier (RF + GradientBoost + SVM)
     -> 0 = good, 1 = bad
  4. Return a result dict with label, confidence, and per-feature breakdown

Usage from Django (photos/views.py):
    from ml import pipeline
    result = pipeline.predict('/absolute/path/to/photo.jpg')
    # result = {
    #   'result':     'pass' | 'fail' | 'pending',
    #   'confidence': 0.94,
    #   'features':   {...},
    #   'issues':     [...],
    #   'use_case':   'general',
    # }

Models live in  ml/models/photo_classifier.pkl
                ml/models/photo_scaler.pkl
"""

import os
import sys
import joblib
import numpy as np

# Add ml/ to path so features.py can be imported
sys.path.insert(0, os.path.dirname(__file__))
from features import extract_features

BASE_DIR        = os.path.dirname(__file__)
MODELS_DIR      = os.path.join(BASE_DIR, 'models')
CLASSIFIER_PATH = os.path.join(MODELS_DIR, 'photo_classifier.pkl')
SCALER_PATH     = os.path.join(MODELS_DIR, 'photo_scaler.pkl')

FEATURE_NAMES = [
    'laplacian_var',
    'center_sharpness',
    'sobel_var',
    'fft_mean',
    'brightness',
    'brightness_std',
    'is_too_dark',
    'is_too_bright',
    'contrast',
    'noise',
    'saturation',
    'l_mean',
    'a_mean',
    'b_mean',
    'entropy',
    'blown',
    'crushed',
    'local_contrast',
]

# ── In-memory model cache ─────────────────────────────────────────────
_model  = None
_scaler = None


def _load_models():
    """Load classifier + scaler from disk. Cached after first call."""
    global _model, _scaler

    if _model is not None and _scaler is not None:
        return True

    if not os.path.exists(CLASSIFIER_PATH):
        print(f'[Pipeline] Model not found at {CLASSIFIER_PATH}')
        return False
    if not os.path.exists(SCALER_PATH):
        print(f'[Pipeline] Scaler not found at {SCALER_PATH}')
        return False

    try:
        _model  = joblib.load(CLASSIFIER_PATH)
        _scaler = joblib.load(SCALER_PATH)
        print(f'[Pipeline] Loaded ensemble model ({len(_model.estimators_)} classifiers, '
              f'{_model.estimators_[0].n_features_in_} features)')
        return True
    except Exception as e:
        print(f'[Pipeline] Failed to load models: {e}')
        return False


def predict(image_path: str) -> dict:
    """
    Full pipeline: image path -> classification result.

    Returns dict:
        result      : 'pass' | 'fail' | 'pending'
        confidence  : float 0-1
        use_case    : 'general'
        features    : dict of named feature values
        issues      : list of human-readable quality warnings
    """
    # 1. Load models
    if not _load_models():
        return _pending(image_path, reason='Models not loaded')

    # 2. Extract features
    try:
        feat_values = extract_features(image_path)
    except Exception as e:
        print(f'[Pipeline] Feature extraction failed for {image_path}: {e}')
        return _pending(image_path, reason=f'Feature extraction error: {e}')

    # 3. Scale
    try:
        feat_array  = np.array(feat_values).reshape(1, -1)
        feat_scaled = _scaler.transform(feat_array)
    except Exception as e:
        print(f'[Pipeline] Scaling failed: {e}')
        return _pending(image_path, reason=f'Scaling error: {e}')

    # 4. Predict
    # NOTE: model trained with label 0=good, 1=bad
    # pipeline returns 'pass' for good, 'fail' for bad
    try:
        prediction = _model.predict(feat_scaled)[0]       # 0=good, 1=bad
        proba      = _model.predict_proba(feat_scaled)[0]  # [p_good, p_bad]
        confidence = float(max(proba))
        result     = 'pass' if prediction == 0 else 'fail'
    except Exception as e:
        print(f'[Pipeline] Prediction failed: {e}')
        return _pending(image_path, reason=f'Prediction error: {e}')

    # 5. Build feature dict + issues
    feat_dict = dict(zip(FEATURE_NAMES, feat_values))
    issues    = _detect_issues(feat_dict)

    print(f'[Pipeline] {os.path.basename(image_path)} -> {result} '
          f'({confidence:.0%} confidence)')

    return {
        'result':     result,
        'confidence': round(confidence, 4),
        'use_case':   'general',
        'features':   {k: round(v, 3) for k, v in feat_dict.items()},
        'issues':     issues,
    }


def reload_models():
    """Force reload models from disk (call after retraining)."""
    global _model, _scaler
    _model  = None
    _scaler = None
    return _load_models()


# ── Helpers ───────────────────────────────────────────────────────────

def _pending(image_path: str, reason: str = '') -> dict:
    return {
        'result':     'pending',
        'confidence': 0.0,
        'use_case':   'unknown',
        'features':   {},
        'issues':     [reason] if reason else [],
    }


def _detect_issues(feat: dict) -> list:
    """Translate feature values into plain-English quality warnings."""
    issues = []

    if feat.get('laplacian_var', 999) < 100:
        issues.append('Image appears blurry (low sharpness)')

    if feat.get('brightness', 128) < 60:
        issues.append('Image is underexposed (too dark)')
    elif feat.get('brightness', 128) > 220:
        issues.append('Image is overexposed (too bright)')

    if feat.get('noise', 0) > 5:
        issues.append('High noise / grain detected')

    if feat.get('contrast', 999) < 40:
        issues.append('Low contrast (flat image)')

    if feat.get('saturation', 999) < 20:
        issues.append('Very low colour saturation')

    if feat.get('blown', 0) > 0.05:
        issues.append('Blown highlights detected (overexposed areas)')

    if feat.get('crushed', 0) > 0.05:
        issues.append('Crushed shadows detected (underexposed areas)')

    if feat.get('local_contrast', 999) < 3:
        issues.append('Low local detail / soft image')

    return issues
