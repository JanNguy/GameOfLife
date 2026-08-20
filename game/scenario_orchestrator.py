from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_server_environment() -> None:
    env_path = Path(__file__).resolve().parent.parent / "serveur" / ".env"
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", maxsplit=1)
        os.environ.setdefault(name.strip(), value.strip())


load_server_environment()


OLLAMA_DEFAULT_BASE_URL = "https://api.ollama.com/v1"
OLLAMA_DEFAULT_MODEL = "deepseek-v4-flash:cloud"


DEFAULT_QUESTION_BANK = [
    {
        "id": "stay_or_leave",
        "question": "L'agent doit-il rester dans sa zone actuelle ?",
        "domain": "migration",
        "type": "binary",
        "description": "Décision de rester ou de quitter une zone touchée par des changements environnementaux.",
    },
    {
        "id": "build_water_storage",
        "question": "L'agent doit-il investir dans le stockage de l'eau ?",
        "domain": "resource_management",
        "type": "binary",
        "description": "Décision de sécuriser les ressources en eau face à un changement environnemental.",
    },
    {
        "id": "move_to_higher_ground",
        "question": "L'agent doit-il migrer vers une zone plus élevée ?",
        "domain": "migration",
        "type": "binary",
        "description": "Décision de quitter une zone basse ou vulnérable pour une zone plus sûre.",
    },
    {
        "id": "restructure_work",
        "question": "L'agent doit-il changer de travail ou de profession ?",
        "domain": "employment",
        "type": "binary",
        "description": "Décision de s'adapter à un environnement économique ou écologique transformé.",
    },
    {
        "id": "invest_in_housing",
        "question": "L'agent doit-il investir dans sa maison ou son logement ?",
        "domain": "housing",
        "type": "binary",
        "description": "Décision de sécuriser ou réaménager son habitation.",
    },
    {
        "id": "change_relationship_plan",
        "question": "L'agent doit-il revoir son plan de vie familiale ou relationnel ?",
        "domain": "relationship",
        "type": "binary",
        "description": "Décision de recalibrer les engagements personnels en fonction du contexte.",
    },
]


MARKET_CRASH_QUESTION_BANK = [
    {
        "id": "investment",
        "question": "L'agent doit-il investir dans des actifs fortement dépréciés ?",
        "domain": "finance",
        "type": "binary",
        "description": "Décision de prendre un risque financier pendant le crash boursier.",
    },
    {
        "id": "employment",
        "question": "L'agent doit-il chercher un travail ou une activité plus résiliente ?",
        "domain": "employment",
        "type": "binary",
        "description": "Décision d'adapter ses revenus face au ralentissement économique.",
    },
    {
        "id": "housing",
        "question": "L'agent doit-il conserver son logement malgré la baisse des prix ?",
        "domain": "housing",
        "type": "binary",
        "description": "Décision de stabiliser son logement pendant la crise financière.",
    },
    {
        "id": "stay_or_leave",
        "question": "L'agent doit-il rester dans son secteur économique actuel ?",
        "domain": "employment",
        "type": "binary",
        "description": "Décision de rester ou de se réorienter après le crash.",
    },
]


APOCALYPSE_QUESTION_BANK = [
    {
        "id": "build_shelter",
        "question": "L'agent doit-il consacrer ses ressources à un abri autonome ?",
        "domain": "survival",
        "type": "binary",
        "description": "Décision de sécuriser un refuge face à l'effondrement des infrastructures.",
    },
    {
        "id": "stock_resources",
        "question": "L'agent doit-il constituer des réserves de nourriture, d'eau et de soins ?",
        "domain": "survival",
        "type": "binary",
        "description": "Décision de réduire la dépendance aux ressources devenues rares.",
    },
    {
        "id": "employment",
        "question": "L'agent doit-il rejoindre une activité locale indispensable à la survie ?",
        "domain": "employment",
        "type": "binary",
        "description": "Décision de contribuer à une économie locale de crise.",
    },
    {
        "id": "move_to_higher_ground",
        "question": "L'agent doit-il quitter sa zone pour rejoindre un refuge plus sûr ?",
        "domain": "migration",
        "type": "binary",
        "description": "Décision de se déplacer malgré les risques du trajet.",
    },
]


def _ensure_question_shape(question: dict[str, Any]) -> dict[str, Any]:
    question = dict(question)
    question.setdefault("id", f"binary_question_{len(question)}")
    question.setdefault("type", "binary")
    question.setdefault("domain", "general")
    question.setdefault("question", "Question de décision binaire non spécifiée.")
    question.setdefault("description", "")
    if question.get("type") != "binary":
        question["type"] = "binary"
    return question


def generate_questions_for_context(context: str, max_questions: int = 5) -> list[dict[str, Any]]:
    """Generate a contextual set of binary questions."""
    normalized = (context or "").lower()
    selected: list[dict[str, Any]] = []

    if any(term in normalized for term in ("fin du monde", "apocalypse", "nuclé", "nucle", "météor", "meteor", "extinction", "zombie")):
        relevant = APOCALYPSE_QUESTION_BANK
    elif any(term in normalized for term in ("bours", "krach", "crash", "marché", "marche financier", "finance")):
        relevant = MARKET_CRASH_QUESTION_BANK
    elif "eau" in normalized or "water" in normalized or "inond" in normalized or "pluie" in normalized:
        relevant = [
            q for q in DEFAULT_QUESTION_BANK if q["domain"] in {"migration", "resource_management", "housing"}
        ]
    elif "travail" in normalized or "emploi" in normalized or "job" in normalized:
        relevant = [
            q for q in DEFAULT_QUESTION_BANK if q["domain"] in {"employment", "migration"}
        ]
    elif "famille" in normalized or "relation" in normalized:
        relevant = [
            q for q in DEFAULT_QUESTION_BANK if q["domain"] in {"relationship", "housing"}
        ]
    else:
        relevant = DEFAULT_QUESTION_BANK[:]

    for question in relevant:
        selected.append(_ensure_question_shape(question))
        if len(selected) >= max_questions:
            break

    return selected


def build_llm_prompt_for_context(context: str, max_questions: int = 5) -> str:
    return (
        "Tu es un orchestrateur de simulation multi-agents. "
        "À partir du contexte donné, propose des questions binaires pertinentes pour la décision de chaque agent. "
        "Retourne uniquement un JSON valide sous forme de liste d'objets avec ces champs : "
        "id, question, domain, type, description. "
        "Le type doit être 'binary'. "
        f"Contexte : {context}\n"
        f"Nombre max de questions : {max_questions}."
    )


def call_orchestrator_llm(context: str, max_questions: int = 5) -> list[dict[str, Any]]:
    """Use Ollama cloud models when OLLAMA_KEY is present; fallback to the rule-based generator otherwise."""
    api_key = os.getenv("OLLAMA_KEY")
    if not api_key:
        return generate_questions_for_context(context, max_questions=max_questions)

    try:
        import requests

        base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_DEFAULT_BASE_URL).rstrip("/")
        model = os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un superviseur de simulation. Propose des questions binaires pertinentes au contexte. Retourne uniquement du JSON valide sous forme de liste d'objets.",
                },
                {"role": "user", "content": build_llm_prompt_for_context(context, max_questions=max_questions)},
            ],
            "temperature": 0.3,
            "max_tokens": 800,
        }
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        payload_response = response.json()

        if isinstance(payload_response, dict):
            if "choices" in payload_response:
                content = payload_response["choices"][0]["message"]["content"]
            elif "message" in payload_response:
                content = payload_response["message"]["content"]
            else:
                content = json.dumps(payload_response)

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                text = content.strip()
                if text.startswith("["):
                    data = json.loads(text)
                else:
                    return generate_questions_for_context(context, max_questions=max_questions)

            if isinstance(data, list):
                return [_ensure_question_shape(item) for item in data]

    except Exception:
        pass

    return generate_questions_for_context(context, max_questions=max_questions)
