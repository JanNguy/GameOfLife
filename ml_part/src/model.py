from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

BASE_DIR   = Path(__file__).resolve().parent.parent        # → ml_part/
MODEL_PATH = BASE_DIR / "out" / "models" / "decision_model.keras"
PREP_PATH  = BASE_DIR / "out" / "models" / "preprocessor.joblib"
DATA_PATH  = Path(__file__).resolve().parent.parent.parent / "data_part" / "out" / "out_profiles.csv"

HIGH_EDU = {"Bachelors", "Masters", "Doctorate", "Prof-school"}
HIGH_OCC = {"Exec-managerial", "Prof-specialty"}

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

df = pd.read_csv(DATA_PATH)
df["occupation"] = df["occupation"].fillna("Unknown")
df["action"]     = (df.apply(compute_score, axis=1) >= 5).astype(int)

print(f"Distribution  →  0: {(df['action']==0).sum()}  |  1: {(df['action']==1).sum()}")
print(f"Taux classe 1 : {df['action'].mean():.1%}\n")

CAT_COLS = ["race", "education", "marital_status", "occupation", "relationship"]
NUM_COLS = ["age", "sample_size", "capital_gain_mean"]

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_COLS),
    ("num", StandardScaler(), NUM_COLS),
])

X = df[CAT_COLS + NUM_COLS]
y = df["action"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

X_train = preprocessor.fit_transform(X_train).astype("float32")
X_test  = preprocessor.transform(X_test).astype("float32")
y_train = y_train.astype("float32").values
y_test  = y_test.astype("float32").values

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(preprocessor, PREP_PATH)
print(f"Preprocessor sauvegardé → {PREP_PATH}")

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(X_train.shape[1],)),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(1,  activation="sigmoid"),
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=3e-4),
    loss="binary_crossentropy",
    metrics=["accuracy"],
)

early_stop = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss", patience=8, restore_best_weights=True, verbose=1
)

model.fit(X_train, y_train, epochs=100, batch_size=32,
          validation_split=0.2, callbacks=[early_stop], verbose=1)

loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\nTest accuracy : {acc:.4f}  |  Loss : {loss:.4f}")

model.save(MODEL_PATH)
print(f"Modèle sauvegardé → {MODEL_PATH}")