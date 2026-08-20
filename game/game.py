"""
game/game.py
Samples N initial agents from out_profiles.csv and runs a binary decision simulation for the current scenario.
"""
import argparse
import json
import random
from pathlib import Path

import pandas as pd

from scenario_orchestrator import call_orchestrator_llm
from decision_engine import simulate_story

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
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scenario", default="default scenario")
    parser.add_argument("--out", default=str(ROOT / "game" / "agents.json"))
    args = parser.parse_args()

    agents = generate_agents(args.n, args.seed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)

    print(f"scenario: {args.scenario}")
    print(f"{len(agents)} agents générés → {args.out}")
    for a in agents:
        print(f"  {a['agent_id']} | {a['race']}, {a['age']} ans, {a['education']}, {a['occupation']}")

    questions = call_orchestrator_llm(args.scenario, max_questions=4)
    print("\nQuestions proposées:")
    for q in questions:
        print(f"  - {q['id']}: {q['question']}")

    story = simulate_story(agents, args.scenario, questions)
    print("\nHistoire de la simulation:")
    for chapter in story.chapters:
        print(f"  {chapter}")

    print("\nTrajectoires des agents:")
    for outcome in story.outcomes:
        print(f"\n  {outcome.agent_id}")
        for event in outcome.timeline:
            print(f"    - {event}")

    print("\nClassement final:")
    for position, outcome in enumerate(story.ranking, start=1):
        status = "survit" if outcome.survived else "en difficulté critique"
        print(
            f"  {position}. {outcome.agent_id} | {outcome.wealth:,.0f} EUR | "
            f"stabilité {outcome.stability:.0f}/100 | {status}"
        )
    print(f"\nBilan : {story.survivor_count} survivant(s), {story.casualty_count} disparition(s).")