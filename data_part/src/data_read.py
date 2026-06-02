import pandas as pd


def keep_latest_value(df: pd.DataFrame) -> pd.DataFrame:
    if "Year" not in df.columns or "Entity" not in df.columns:
        return df.copy()

    return (
        df.sort_values(["Entity", "Year"])
        .drop_duplicates(subset=["Entity"], keep="last")
        .reset_index(drop=True)
    )


df_capital = pd.read_csv("Data/train.csv", chunksize=1000000)
df_capital = pd.concat(list(df_capital), ignore_index=True)

# --- education ---
df_education = (
    df_capital.groupby("education")
    .size()
    .reset_index(name="count")
)
df_education["probability"] = df_education["count"] / df_education["count"].sum() * 100
df_education = df_education.sort_values("probability", ascending=False).reset_index(drop=True)
df_education.to_csv("out/out_education.csv", index=False)

# --- marital status ---
df_marital = (
    df_capital.groupby("marital_status")
    .size()
    .reset_index(name="count")
)
df_marital["probability"] = df_marital["count"] / df_marital["count"].sum() * 100
df_marital = df_marital.sort_values("probability", ascending=False).reset_index(drop=True)
df_marital.to_csv("out/out_marital.csv", index=False)

# --- occupation ---
df_occupation = (
    df_capital.groupby("occupation")
    .size()
    .reset_index(name="count")
)
df_occupation["probability"] = df_occupation["count"] / df_occupation["count"].sum() * 100
df_occupation = df_occupation.sort_values("probability", ascending=False).reset_index(drop=True)
df_occupation.to_csv("out/out_occupation.csv", index=False)

# --- relationship ---
df_relationship = (
    df_capital.groupby("relationship")
    .size()
    .reset_index(name="count")
)
df_relationship["probability"] = df_relationship["count"] / df_relationship["count"].sum() * 100
df_relationship = df_relationship.sort_values("probability", ascending=False).reset_index(drop=True)
df_relationship.to_csv("out/out_relationship.csv", index=False)

# --- race ---
df_race = (
    df_capital.groupby("race")
    .size()
    .reset_index(name="count")
)
df_race["probability"] = df_race["count"] / df_race["count"].sum() * 100
df_race = df_race.sort_values("probability", ascending=False).reset_index(drop=True)
df_race.to_csv("out/out_race.csv", index=False)

# --- capital gain par race ---
df_capital_gain_race = (
    df_capital.groupby("race")["capital_gain"]
    .agg(mean_capital_gain="mean", count="count")
    .reset_index()
)
df_capital_gain_race["probability"] = df_capital_gain_race["count"] / df_capital_gain_race["count"].sum() * 100
df_capital_gain_race = df_capital_gain_race.sort_values("mean_capital_gain", ascending=False).reset_index(drop=True)
df_capital_gain_race.to_csv("out/out_capital_gain_by_race.csv", index=False)

print("Fichiers générés dans out/:")
print("  out/out_education.csv")
print("  out/out_marital.csv")
print("  out/out_occupation.csv")
print("  out/out_relationship.csv")
print("  out/out_race.csv")
print("  out/out_capital_gain_by_race.csv")
