"""
game/game.py
Samples N initial agents from out_profiles.csv.
"""
import argparse
import json
import random
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

def generate_agents(n: int, seed: int = 42) -> list[dict]:
    random.seed(seed)
    df = pd.read_csv(ROOT / "data_part" / "out" / "out_profiles.csv")
    df["occupation"] = df["occupation"].fillna("Unknown")

    agents = []
    sample = df.sample(n=min(n, len(df)), random_state=seed)

    for i, (_, row) in enumerate(sample.iterrows()):
        agents.append({
            "agent_id":         f"agent_{i:03d}",
            "race":             row["race"],
            "age":              int(row["age"]),
            "education":        row["education"],
            "marital_status":   row["marital_status"],
            "occupation":       str(row["occupation"]),
            "relationship":     row["relationship"],
            "capital_gain_mean": float(row["capital_gain_mean"]),
            "sample_size":      int(row["sample_size"]),
            "income_rate":      float(row.get("income_rate", 0.0)),
        })
    return agents

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n",    type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out",  default=str(ROOT / "game" / "agents.json"))
    args = parser.parse_args()

    agents = generate_agents(args.n, args.seed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)
    print(f"{len(agents)} agents générés → {args.out}")
    for a in agents:
        print(f"  {a['agent_id']} | {a['race']}, {a['age']} ans, {a['education']}, {a['occupation']}")