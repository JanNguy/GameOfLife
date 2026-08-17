from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "out" / "models" / "decision_model_multihead.keras"
PREP_PATH = BASE_DIR / "out" / "models" / "preprocessor.joblib"
DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data_part" / "out" / "out_profiles.csv"

HIGH_EDU = {"Bachelors", "Masters", "Doctorate", "Prof-school"}
HIGH_OCC = {"Exec-managerial", "Prof-specialty"}

def compute_score(row):
    s = 0
    if row["education"] in HIGH_EDU:
        s += 2
    if 30 <= row["age"] <= 60:
        s += 2
    if row["occupation"] in HIGH_OCC:
        s += 2
    if row["capital_gain_mean"] > 1000:
        s += 2
    if row["capital_gain_mean"] > 3000:
        s += 1
    if row["marital_status"] == "Married-civ-spouse":
        s += 1
    if row["relationship"] in {"Husband", "Wife"}:
        s += 1
    return s

def get_level(score):
    if score <= 2:
        return 0
    elif score <= 4:
        return 1
    elif score <= 6:
        return 2
    else:
        return 3

df = pd.read_csv(DATA_PATH)
df["occupation"] = df["occupation"].fillna("Unknown")
df["score"] = df.apply(compute_score, axis=1)
df["action"] = (df["score"] >= 5).astype(int)
df["level"] = df["score"].apply(get_level)

print(f"Distribution action → 0: {(df['action']==0).sum()} | 1: {(df['action']==1).sum()}")
print(f"Taux classe 1 : {df['action'].mean():.1%}")
print(f"Distribution level →\n{df['level'].value_counts().sort_index()}")

CAT_COLS = ["race", "education", "marital_status", "occupation", "relationship"]
NUM_COLS = ["age", "sample_size", "capital_gain_mean"]

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_COLS),
    ("num", StandardScaler(), NUM_COLS),
])

X = df[CAT_COLS + NUM_COLS]
y_binary = df["action"]
y_multi = df["level"]

X_train, X_test, y_binary_train, y_binary_test, y_multi_train, y_multi_test = train_test_split(
    X, y_binary, y_multi, test_size=0.2, random_state=42, stratify=y_binary
)

X_train = preprocessor.fit_transform(X_train).astype("float32")
X_test = preprocessor.transform(X_test).astype("float32")

y_binary_train = y_binary_train.astype("float32").values
y_binary_test = y_binary_test.astype("float32").values
y_multi_train = y_multi_train.astype("int32").values
y_multi_test = y_multi_test.astype("int32").values

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(preprocessor, PREP_PATH)
print(f"Preprocessor sauvegardé → {PREP_PATH}")

# Modèle multi-têtes (sans stop_gradient)
inputs = tf.keras.Input(shape=(X_train.shape[1],))

shared = tf.keras.layers.Dense(64, activation="relu")(inputs)
shared = tf.keras.layers.Dropout(0.2)(shared)
shared = tf.keras.layers.Dense(32, activation="relu")(shared)

binary_out = tf.keras.layers.Dense(1, activation="sigmoid", name="binary")(shared)

# Concaténation directe (pas de stop_gradient)
concat = tf.keras.layers.Concatenate()([shared, binary_out])

multi = tf.keras.layers.Dense(64, activation="relu")(concat)
multi = tf.keras.layers.Dropout(0.2)(multi)
multi_out = tf.keras.layers.Dense(4, activation="softmax", name="multi")(multi)

model = tf.keras.Model(inputs=inputs, outputs=[binary_out, multi_out])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=3e-4),
    loss={
        "binary": "binary_crossentropy",
        "multi": "sparse_categorical_crossentropy"
    },
    metrics={
        "binary": ["accuracy"],
        "multi": ["accuracy"]
    },
    loss_weights={"binary": 1.0, "multi": 0.5}   # on donne plus d'importance à la binaire
)

early_stop = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss", patience=8, restore_best_weights=True, verbose=1
)

history = model.fit(
    X_train,
    {"binary": y_binary_train, "multi": y_multi_train},
    epochs=100,
    batch_size=32,
    validation_split=0.2,
    callbacks=[early_stop],
    verbose=1
)

eval_results = model.evaluate(X_test, {"binary": y_binary_test, "multi": y_multi_test}, verbose=0)
print(f"\nTest - binary loss: {eval_results[1]:.4f}, binary acc: {eval_results[2]:.4f}")
print(f"Test - multi loss: {eval_results[3]:.4f}, multi acc: {eval_results[4]:.4f}")

model.save(MODEL_PATH)
print(f"Modèle multi-têtes sauvegardé → {MODEL_PATH}")