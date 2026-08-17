from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from tensorflow.keras.layers import Input, Dense, Dropout, Concatenate
from tensorflow.keras.models import Model

# ------------------------------
# 1. Chemins et constantes
# ------------------------------
BASE_DIR   = Path(__file__).resolve().parent.parent        # → ml_part/
MODEL_PATH = BASE_DIR / "out" / "models" / "decision_model_multihead.keras"
PREP_PATH  = BASE_DIR / "out" / "models" / "preprocessor.joblib"
DATA_PATH  = Path(__file__).resolve().parent.parent.parent / "data_part" / "out" / "out_profiles.csv"

HIGH_EDU = {"Bachelors", "Masters", "Doctorate", "Prof-school"}
HIGH_OCC = {"Exec-managerial", "Prof-specialty"}

# ------------------------------
# 2. Calcul du score et des cibles
# ------------------------------
def compute_score(row):
    s = 0
    if row["education"]         in HIGH_EDU:             s += 2
    if 30 <= row["age"] <= 60:                            s += 2
    if row["occupation"]        in HIGH_OCC:              s += 2
    if row["capital_gain_mean"] > 1000:                   s += 2
    if row["capital_gain_mean"] > 3000:                   s += 1
    if row["marital_status"]    == "Married-civ-spouse":  s += 1
    if row["relationship"]      in {"Husband", "Wife"}:   s += 1
    return s

def get_decision_level(score):
    """Transforme le score en niveau de décision (0 à 3)"""
    if score <= 2:
        return 0   # Refus total
    elif score <= 4:
        return 1   # Refus modéré
    elif score <= 6:
        return 2   # Acceptation avec réserve
    else:
        return 3   # Acceptation forte

# Chargement et création des cibles
df = pd.read_csv(DATA_PATH)
df["occupation"] = df["occupation"].fillna("Unknown")
df["score"]      = df.apply(compute_score, axis=1)
df["action"]     = (df["score"] >= 5).astype(int)          # cible binaire
df["level"]      = df["score"].apply(get_decision_level)   # cible multi-classe (0-3)

print(f"Distribution binaire → 0: {(df['action']==0).sum()}  |  1: {(df['action']==1).sum()}")
print(f"Taux classe 1 : {df['action'].mean():.1%}")
print("\nNiveaux de décision :")
print(df["level"].value_counts().sort_index())

# ------------------------------
# 3. Prétraitement (inchangé)
# ------------------------------
CAT_COLS = ["race", "education", "marital_status", "occupation", "relationship"]
NUM_COLS = ["age", "sample_size", "capital_gain_mean"]

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_COLS),
    ("num", StandardScaler(), NUM_COLS),
])

X = df[CAT_COLS + NUM_COLS]
y_binary = df["action"]
y_multi  = df["level"]

X_train, X_test, y_train_bin, y_test_bin = train_test_split(
    X, y_binary, test_size=0.2, random_state=42, stratify=y_binary
)
# On utilise le même split pour la cible multi (sinon on pourrait stratifier aussi)
_, _, y_train_multi, y_test_multi = train_test_split(
    X, y_multi, test_size=0.2, random_state=42, stratify=y_binary
)

# Transformation
X_train = preprocessor.fit_transform(X_train).astype("float32")
X_test  = preprocessor.transform(X_test).astype("float32")

y_train_bin = y_train_bin.astype("float32").values
y_test_bin  = y_test_bin.astype("float32").values
y_train_multi = y_train_multi.astype("int32").values
y_test_multi  = y_test_multi.astype("int32").values

# Sauvegarde du préprocesseur
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(preprocessor, PREP_PATH)
print(f"Preprocessor sauvegardé → {PREP_PATH}")

# ------------------------------
# 4. Modèle multi‑têtes (API fonctionnelle)
# ------------------------------
inputs = Input(shape=(X_train.shape[1],), name="features")

# Tronc commun
shared = Dense(64, activation="relu")(inputs)
shared = Dropout(0.2)(shared)
shared = Dense(32, activation="relu")(shared)

# Tête 1 : classification binaire (action)
binary_out = Dense(1, activation="sigmoid", name="binary")(shared)

# Concaténation du tronc avec la sortie binaire (avec stop_gradient)
# Cela évite que la tête multi‑classe "triche" en utilisant directement le signal binaire
concat = Concatenate(name="concat")([shared, tf.stop_gradient(binary_out)])

# Tête 2 : classification multi‑classe (4 niveaux)
multi = Dense(64, activation="relu")(concat)
multi = Dropout(0.2)(multi)
multi_out = Dense(4, activation="softmax", name="multi")(multi)

# Construction du modèle
model = Model(inputs=inputs, outputs=[binary_out, multi_out])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=3e-4),
    loss={
        "binary": "binary_crossentropy",
        "multi": "sparse_categorical_crossentropy",
    },
    metrics={
        "binary": ["accuracy"],
        "multi": ["accuracy"]
    },
    loss_weights={"binary": 0.5, "multi": 0.5}   # équilibre entre les deux objectifs
)

# Early stopping
early_stop = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss", patience=8, restore_best_weights=True, verbose=1
)

# Entraînement
history = model.fit(
    X_train,
    {"binary": y_train_bin, "multi": y_train_multi},
    epochs=100,
    batch_size=32,
    validation_split=0.2,
    callbacks=[early_stop],
    verbose=1
)

# Évaluation sur le test set
eval_results = model.evaluate(X_test, {"binary": y_test_bin, "multi": y_test_multi}, verbose=0)
print(f"\nTest - binary loss: {eval_results[1]:.4f}, binary acc: {eval_results[2]:.4f}")
print(f"Test - multi loss: {eval_results[3]:.4f}, multi acc: {eval_results[4]:.4f}")

# Sauvegarde du modèle
model.save(MODEL_PATH)
print(f"Modèle multi‑têtes sauvegardé → {MODEL_PATH}")

# ------------------------------
# 5. Exemple d'inférence
# ------------------------------
# On prend les 5 premiers exemples du test
sample = X_test[:5]
prob_bin, prob_multi = model.predict(sample)

niveaux = ["Refus total", "Refus modéré", "Acceptation avec réserve", "Acceptation forte"]
for i in range(5):
    decision_idx = np.argmax(prob_multi[i])
    print(f"Exemple {i+1}: proba acceptation = {prob_bin[i][0]:.3f} → "
          f"Décision finale = {niveaux[decision_idx]} (confiance {prob_multi[i][decision_idx]:.2f})")