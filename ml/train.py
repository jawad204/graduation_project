"""
train.py
--------
Retrains the photo quality classifier and saves:
    ml/models/photo_classifier.pkl
    ml/models/photo_scaler.pkl

Dataset layout expected:
    <GOOD_DIR>/   — original good photos from photographer (label = 0)
    <BAD_DIR>/    — synthetic bad photos (label = 1)

Run:
    cd photobook_v2
    python ml/train.py

After training, restart Django so the new models are loaded.
"""

import os
import sys
import warnings
import numpy as np
from sklearn.ensemble import (RandomForestClassifier,
                               GradientBoostingClassifier,
                               VotingClassifier)
from sklearn.svm import SVC
from sklearn.model_selection import (train_test_split,
                                     StratifiedKFold,
                                     cross_val_score)
from sklearn.metrics import (classification_report,
                              accuracy_score,
                              roc_auc_score,
                              confusion_matrix)
from sklearn.preprocessing import StandardScaler
import joblib

warnings.filterwarnings('ignore')

# ── CONFIG ────────────────────────────────────────────────────────────
GOOD_DIR   = r"C:\path\to\good"   # ← change to your good images folder
BAD_DIR    = r"C:\path\to\bad"    # ← change to your bad images folder
SEED       = 42
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)
# ─────────────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.dirname(__file__))
from features import extract_features

EXTS = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')

# ── LOAD DATASET ─────────────────────────────────────────────────────
print("=" * 60)
print("  LOADING DATASET")
print("=" * 60)
X, y = [], []

print("  Loading good photos (label=0)...")
for i, f in enumerate(sorted(os.listdir(GOOD_DIR))):
    if f.endswith(EXTS):
        try:
            feat = extract_features(os.path.join(GOOD_DIR, f))
            X.append(feat); y.append(0)
        except Exception as e:
            print(f"    Skip {f}: {e}")
    if (i + 1) % 200 == 0:
        print(f"    {i+1} processed...")

print("  Loading bad photos (label=1)...")
for i, f in enumerate(sorted(os.listdir(BAD_DIR))):
    if f.endswith(EXTS):
        try:
            feat = extract_features(os.path.join(BAD_DIR, f))
            X.append(feat); y.append(1)
        except Exception as e:
            print(f"    Skip {f}: {e}")
    if (i + 1) % 200 == 0:
        print(f"    {i+1} processed...")

X = np.array(X); y = np.array(y)
print(f"\n  Good: {(y==0).sum()} | Bad: {(y==1).sum()} | Total: {len(y)}")
print(f"  Feature vector size: {X.shape[1]}")

# ── SPLIT 70 / 15 / 15 ───────────────────────────────────────────────
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.30, random_state=SEED, stratify=y)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, random_state=SEED, stratify=y_temp)

scaler    = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_val_s   = scaler.transform(X_val)
X_test_s  = scaler.transform(X_test)
X_all_s   = scaler.transform(X)

print(f"\n  Train: {len(y_train)} | Val: {len(y_val)} | Test: {len(y_test)}")

# ── MODELS ────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  TRAINING ENSEMBLE (RF + GradientBoost + SVM)")
print("=" * 60)

rf = RandomForestClassifier(
    n_estimators     = 500,
    max_depth        = 12,
    min_samples_leaf = 4,
    min_samples_split= 8,
    max_features     = 'sqrt',
    random_state     = SEED,
    n_jobs           = -1,
    class_weight     = 'balanced'
)

gb = GradientBoostingClassifier(
    n_estimators  = 300,
    max_depth     = 3,
    learning_rate = 0.03,
    subsample     = 0.75,
    max_features  = 'sqrt',
    random_state  = SEED,
)

svm = SVC(
    kernel      = 'rbf',
    C           = 0.8,
    gamma       = 'scale',
    probability = True,
    random_state= SEED,
)

model = VotingClassifier(
    estimators = [('rf', rf), ('gb', gb), ('svm', svm)],
    voting     = 'soft',
    n_jobs     = -1,
)

model.fit(X_train_s, y_train)
print("  ✅ Training complete!")

# ── EVALUATE ─────────────────────────────────────────────────────────
def evaluate(X_e, y_e, name):
    y_pred  = model.predict(X_e)
    y_proba = model.predict_proba(X_e)[:, 1]
    acc     = accuracy_score(y_e, y_pred)
    auc     = roc_auc_score(y_e, y_proba)
    cm      = confusion_matrix(y_e, y_pred)
    print(f"\n{'='*60}\n  {name}\n{'='*60}")
    print(f"  Accuracy : {acc:.1%}")
    print(f"  AUC-ROC  : {auc:.4f}")
    print(classification_report(y_e, y_pred, target_names=["good", "bad"]))
    print(f"  Confusion Matrix: TP={cm[1][1]} TN={cm[0][0]} FP={cm[0][1]} FN={cm[1][0]}")
    return acc

val_acc  = evaluate(X_val_s,  y_val,  "VALIDATION RESULTS")
test_acc = evaluate(X_test_s, y_test, "TEST RESULTS")

# Cross validation
print(f"\n{'='*60}\n  5-FOLD CROSS VALIDATION\n{'='*60}")
cv        = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
cv_scores = cross_val_score(model, X_all_s, y, cv=cv, scoring='accuracy', n_jobs=-1)
print(f"  Folds : {[f'{s:.1%}' for s in cv_scores]}")
print(f"  Mean  : {cv_scores.mean():.1%} ± {cv_scores.std():.1%}")

# Overfit check
train_acc = accuracy_score(y_train, model.predict(X_train_s))
gap       = train_acc - test_acc
print(f"\n{'='*60}\n  VERDICT\n{'='*60}")
print(f"  Train : {train_acc:.1%} | Test : {test_acc:.1%} | Gap : {gap:.1%}", end=" ")
print("✅" if gap < 0.05 else "⚠️" if gap < 0.10 else "❌")

# ── SAVE ──────────────────────────────────────────────────────────────
clf_path    = os.path.join(MODELS_DIR, 'photo_classifier.pkl')
scaler_path = os.path.join(MODELS_DIR, 'photo_scaler.pkl')
joblib.dump(model,  clf_path,    compress=3)
joblib.dump(scaler, scaler_path, compress=3)
print(f"\n  ✅ Model  saved → {clf_path}")
print(f"  ✅ Scaler saved → {scaler_path}")
print("\n  Restart Django to load the new models.")
