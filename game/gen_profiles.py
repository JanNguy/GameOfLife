import csv
import json
import random
from pathlib import Path


DEFAULT_PROFILE_COUNT = 10
DEFAULT_CSV_PATH = "../data_part/out/out_profiles.csv"
DEFAULT_JSON_PATH = "../data_part/out/out_profiles.json"


# ----------------------------
# LOAD CSV
# ----------------------------
def load_profiles_with_probabilities(csv_path: str = DEFAULT_CSV_PATH):
    path = Path(csv_path)
    rows = []

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            clean = {}

            for k, v in row.items():
                if k is None or v is None:
                    continue

                key = k.strip()
                val = v.strip()

                # remove %
                val = val.replace("%", "").strip()

                # convert types
                try:
                    if "." in val:
                        val = float(val)
                    else:
                        val = int(val)
                except ValueError:
                    pass

                clean[key] = val

            rows.append(clean)

    return rows


# ----------------------------
# BUILD DISTRIBUTIONS
# ----------------------------
def build_distribution(profiles, field):
    """
    Build weighted distribution for a categorical field
    using implicit frequency in dataset.
    """
    counter = {}

    for p in profiles:
        if field in p:
            counter[p[field]] = counter.get(p[field], 0) + 1

    values = list(counter.keys())
    weights = list(counter.values())

    return values, weights


def sample_from_distribution(values, weights):
    return random.choices(values, weights=weights, k=1)[0]


# ----------------------------
# GENERATE ONE SYNTHETIC PROFILE
# ----------------------------
def generate_profile(profiles):
    # build distributions
    races, race_w = build_distribution(profiles, "race")
    educs, edu_w = build_distribution(profiles, "education")
    marital, marital_w = build_distribution(profiles, "marital_status")
    occs, occ_w = build_distribution(profiles, "occupation")
    rels, rel_w = build_distribution(profiles, "relationship")

    base = random.choice(profiles)

    return {
        "race": sample_from_distribution(races, race_w),
        "age": int(base.get("age", random.randint(18, 80))),
        "sample_size": int(base.get("sample_size", 1)),
        "capital_gain_mean": float(base.get("capital_gain_mean", 0.0)),

        "education": sample_from_distribution(educs, edu_w),
        "marital_status": sample_from_distribution(marital, marital_w),
        "occupation": sample_from_distribution(occs, occ_w),
        "relationship": sample_from_distribution(rels, rel_w),
    }


# ----------------------------
# GENERATE MANY PROFILES
# ----------------------------
def generate_human_profiles(count=DEFAULT_PROFILE_COUNT, csv_path=DEFAULT_CSV_PATH):
    base_profiles = load_profiles_with_probabilities(csv_path)

    if not base_profiles:
        return []

    return [generate_profile(base_profiles) for _ in range(count)]


# ----------------------------
# SAVE
# ----------------------------
def save_profiles_to_json(profiles, json_path=DEFAULT_JSON_PATH):
    path = Path(json_path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    profiles = generate_human_profiles(10)
    save_profiles_to_json(profiles)

    for p in profiles:
        print(p)