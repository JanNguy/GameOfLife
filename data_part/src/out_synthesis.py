import pandas as pd

# Population complète
df = pd.read_csv("Data/train.csv", chunksize=1000000)
df = pd.concat(list(df), ignore_index=True)
df["occupation"] = df["occupation"].fillna("Unknown")

FIELDS = ["education", "marital_status", "occupation", "relationship"]

rows = []
for (race, age), grp in df.groupby(["race", "age"]):
    row = {"race": race, "age": age, "sample_size": len(grp)}
    row["capital_gain_mean"] = round(grp["capital_gain"].mean(), 0)
    row["income_rate"] = round(grp["income_supp_50K"].mean() * 100, 1)  # % réel >50K

    for field in FIELDS:
        clean = grp[field].dropna()
        if clean.empty:
            row[field] = None
            row[f"{field}_prob%"] = None
            continue
        probs = clean.value_counts(normalize=True) * 100
        top   = probs.idxmax()
        row[field]            = top
        row[f"{field}_prob%"] = round(probs[top], 1)

    rows.append(row)

cols = [
    "race", "age", "sample_size", "capital_gain_mean", "income_rate",
    "education",      "education_prob%",
    "marital_status", "marital_status_prob%",
    "occupation",     "occupation_prob%",
    "relationship",   "relationship_prob%",
]

out = (
    pd.DataFrame(rows, columns=cols)
    .sort_values(["race", "age"])
    .reset_index(drop=True)
)
out.to_csv("out/out_profiles.csv", index=False)
print(f"out_profiles.csv — {len(out)} lignes x {len(out.columns)} colonnes")
print(out.head(10).to_string())