from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable


DECISION_TYPES = {
    "employment": {
        "description": "agent accepts an employment opportunity",
        "threshold": 0.62,
    },
    "housing": {
        "description": "agent accepts a housing opportunity",
        "threshold": 0.58,
    },
    "relationship": {
        "description": "agent accepts a committed relationship",
        "threshold": 0.55,
    },
    "investment": {
        "description": "agent invests in a project or a new activity",
        "threshold": 0.6,
    },
}


@dataclass
class AgentDecision:
    agent_id: str
    decision: str
    accepted: bool
    probability: float
    confidence: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class SimulationSummary:
    total_agents: int
    decisions: dict[str, int]
    acceptance_rate: float
    supervisor_note: str


@dataclass
class StoryOutcome:
    agent_id: str
    wealth: float
    stability: float
    survived: bool
    timeline: list[str]


@dataclass
class StorySimulation:
    scenario_kind: str
    chapters: list[str]
    outcomes: list[StoryOutcome]
    ranking: list[StoryOutcome]
    survivor_count: int
    casualty_count: int


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _compute_decision_probability(agent: dict, decision_name: str) -> tuple[float, list[str]]:
    age = _as_float(agent.get("age", 0))
    capital_gain = _as_float(agent.get("capital_gain_mean", 0))
    sample_size = _as_float(agent.get("sample_size", 0))
    education = str(agent.get("education", ""))
    occupation = str(agent.get("occupation", "")).lower()
    relationship = str(agent.get("relationship", "")).lower()
    marital_status = str(agent.get("marital_status", "")).lower()

    score = 0.5
    reasons: list[str] = []

    if 25 <= age <= 60:
        score += 0.12
        reasons.append("age compatible with the decision")
    else:
        reasons.append("age less favorable")

    if capital_gain > 1000:
        score += 0.18
        reasons.append("financial cushion is strong")
    elif capital_gain > 200:
        score += 0.08
        reasons.append("some financial stability")
    else:
        reasons.append("low capital gain")

    if "bachelors" in education.lower() or "masters" in education.lower() or "doctorate" in education.lower():
        score += 0.12
        reasons.append("education supports the decision")

    if "managerial" in occupation or "specialty" in occupation:
        score += 0.10
        reasons.append("occupation is favorable")

    if "husband" in relationship or "wife" in relationship or "married" in marital_status:
        score += 0.08
        reasons.append("family stability is favorable")

    if sample_size > 50:
        score += 0.08
        reasons.append("profile is supported by sufficient sample size")

    if decision_name == "employment":
        if "managerial" in occupation or "specialty" in occupation:
            score += 0.12
        if age < 22 or age > 70:
            score -= 0.14
    elif decision_name == "housing":
        if capital_gain > 1000:
            score += 0.12
        if age < 25:
            score -= 0.08
    elif decision_name == "relationship":
        if "married" in marital_status or "husband" in relationship or "wife" in relationship:
            score += 0.14
        else:
            score -= 0.06
    elif decision_name == "investment":
        if capital_gain > 2000:
            score += 0.16
        if age < 30:
            score += 0.04
        else:
            score -= 0.04

    score = max(0.0, min(1.0, score))
    return round(score, 4), reasons


def _make_decision(agent: dict, decision_name: str, threshold: float | None = None) -> AgentDecision:
    if threshold is None:
        threshold = DECISION_TYPES.get(decision_name, {}).get("threshold", 0.6)

    probability, reasons = _compute_decision_probability(agent, decision_name)
    accepted = probability >= threshold
    confidence = abs(probability - threshold) + 0.5
    confidence = max(0.5, min(0.99, confidence))

    return AgentDecision(
        agent_id=str(agent.get("agent_id", "unknown")),
        decision=decision_name,
        accepted=accepted,
        probability=probability,
        confidence=round(confidence, 4),
        reasons=reasons,
    )


def simulate_round(agents: Iterable[dict], decision_names: Iterable[str] | None = None) -> tuple[list[AgentDecision], SimulationSummary]:
    agent_list = list(agents)
    if decision_names is None:
        decision_names = list(DECISION_TYPES)

    decision_names = list(decision_names)
    decisions: list[AgentDecision] = []
    counts = {name: 0 for name in decision_names}

    for agent in agent_list:
        for decision_name in decision_names:
            result = _make_decision(agent, decision_name)
            decisions.append(result)
            counts[decision_name] += int(result.accepted)

    total = len(decisions)
    accepted_total = sum(int(d.accepted) for d in decisions)
    acceptance_rate = round((accepted_total / total) if total else 0.0, 4)

    strongest = max(decision_names, key=lambda name: counts.get(name, 0))
    weakest = min(decision_names, key=lambda name: counts.get(name, 0))
    supervisor_note = (
        f"The system is most favorable on '{strongest}' and weakest on '{weakest}'. "
        f"Overall acceptance is {acceptance_rate:.2%}."
    )

    summary = SimulationSummary(
        total_agents=len(agent_list),
        decisions=counts,
        acceptance_rate=acceptance_rate,
        supervisor_note=supervisor_note,
    )

    return decisions, summary


def supervisor_summary(decisions: Iterable[AgentDecision]) -> str:
    rows = list(decisions)
    if not rows:
        return "No decisions available for supervision."

    by_decision: dict[str, list[AgentDecision]] = {}
    for row in rows:
        by_decision.setdefault(row.decision, []).append(row)

    summary_lines = ["Superviseur LLM — synthèse de la simulation"]
    for decision_name, items in sorted(by_decision.items()):
        accepted = sum(int(item.accepted) for item in items)
        total = len(items)
        ratio = accepted / total if total else 0.0
        summary_lines.append(
            f"- {decision_name}: {accepted}/{total} acceptés ({ratio:.0%})"
        )

    most_confident = max(rows, key=lambda item: item.confidence)
    summary_lines.append(
        f"- décision la plus sûre: {most_confident.decision} ({most_confident.confidence:.2f})"
    )
    return "\n".join(summary_lines)


def _scenario_kind(scenario: str) -> str:
    normalized = scenario.lower()
    if any(term in normalized for term in ("fin du monde", "apocalypse", "nuclé", "nucle", "météor", "meteor", "extinction", "zombie")):
        return "apocalypse"
    if any(term in normalized for term in ("bours", "krach", "crash", "marché", "marche financier", "finance")):
        return "market_crash"
    if any(term in normalized for term in ("eau", "inond", "sécher", "secher", "pluie")):
        return "water_crisis"
    return "general_crisis"


def _initial_wealth(agent: dict) -> float:
    capital_gain = _as_float(agent.get("capital_gain_mean", 0))
    income_rate = _as_float(agent.get("income_rate", 0))
    education = str(agent.get("education", "")).lower()
    education_bonus = 8000 if any(level in education for level in ("bachelors", "masters", "doctorate")) else 2500
    return round(max(1500, 6000 + capital_gain * 4 + income_rate * 18000 + education_bonus), 2)


def _decision_lookup(decisions: Iterable[AgentDecision]) -> dict[str, dict[str, AgentDecision]]:
    grouped: dict[str, dict[str, AgentDecision]] = {}
    for decision in decisions:
        grouped.setdefault(decision.agent_id, {})[decision.decision] = decision
    return grouped


def simulate_story(agents: Iterable[dict], scenario: str, questions: Iterable[dict]) -> StorySimulation:
    """Run a multi-step simulation and keep a readable branch for each agent."""
    agent_list = list(agents)
    question_list = list(questions)
    decision_names = [question["id"] for question in question_list if question.get("type") == "binary"]
    decisions, _ = simulate_round(agent_list, decision_names or list(DECISION_TYPES))
    by_agent = _decision_lookup(decisions)
    scenario_kind = _scenario_kind(scenario)

    chapters_by_kind = {
        "apocalypse": [
            "Acte I - Les infrastructures s'effondrent et les ressources deviennent rares.",
            "Acte II - Les agents doivent sécuriser un abri, des réserves ou une nouvelle source de revenus.",
            "Acte III - La crise se prolonge : seuls les agents assez stables et équipés restent en vie.",
        ],
        "market_crash": [
            "Acte I - Le marché perd brutalement de sa valeur.",
            "Acte II - Les agents choisissent entre protéger leur épargne et saisir les actifs dépréciés.",
            "Acte III - L'économie se stabilise et les trajectoires financières sont comparées.",
        ],
        "water_crisis": [
            "Acte I - La ressource en eau devient rare et les infrastructures sont sous pression.",
            "Acte II - Les agents choisissent de sécuriser leurs ressources ou de changer de zone.",
            "Acte III - La communauté s'adapte et les trajectoires sont comparées.",
        ],
        "general_crisis": [
            "Acte I - Un choc transforme les conditions de vie des agents.",
            "Acte II - Chaque agent arbitre entre protection, adaptation et prise de risque.",
            "Acte III - Les conséquences de ces choix déterminent la situation finale.",
        ],
    }

    outcomes: list[StoryOutcome] = []
    for agent in agent_list:
        agent_id = str(agent.get("agent_id", "unknown"))
        agent_decisions = by_agent.get(agent_id, {})
        wealth = _initial_wealth(agent)
        stability = 60.0
        timeline = [f"Départ : patrimoine estimé à {wealth:,.0f} EUR et stabilité {stability:.0f}/100."]

        accepts_protection = any(
            decision.accepted
            for name, decision in agent_decisions.items()
            if any(term in name for term in (
                "invest", "water", "housing", "higher_ground", "shelter", "stock", "food", "protect",
            ))
        )
        accepts_work_change = any(
            decision.accepted for name, decision in agent_decisions.items() if "work" in name or "employment" in name
        )
        accepts_migration = any(
            decision.accepted for name, decision in agent_decisions.items() if "move" in name or "leave" in name
        )

        if scenario_kind == "apocalypse":
            infrastructure_loss = wealth * 0.65
            wealth -= infrastructure_loss
            stability -= 58
            timeline.append(
                f"Effondrement : pertes matérielles de {infrastructure_loss:,.0f} EUR et rupture des services essentiels."
            )
            age = _as_float(agent.get("age", 0))
            if age >= 70:
                stability -= 20
                timeline.append("Vulnérabilité accrue : l'âge rend l'accès aux ressources et aux soins plus difficile.")
            if wealth < 5000:
                stability -= 10
                timeline.append("Réserves insuffisantes : l'agent ne peut pas absorber durablement la pénurie.")
            if accepts_protection:
                wealth -= min(3000, wealth * 0.25)
                stability += 25
                timeline.append("Branche protection : abri et réserves sécurisés, la stabilité remonte malgré le coût.")
            else:
                stability -= 12
                timeline.append("Branche exposée : absence de protection, l'agent reste dépendant de ressources instables.")
            if accepts_work_change:
                wealth += 2500
                stability += 10
                timeline.append("Organisation locale : une activité utile procure ressources et soutien (+2,500 EUR).")
            else:
                stability -= 8
                timeline.append("Aucune activité résiliente : les ressources continuent de diminuer.")
        elif scenario_kind == "market_crash":
            loss = wealth * 0.24
            wealth -= loss
            timeline.append(f"Choc boursier : perte initiale de {loss:,.0f} EUR.")
            if accepts_protection:
                recovery = wealth * 0.42
                wealth += recovery
                stability += 12
                timeline.append(f"Branche investissement : des actifs dépréciés rapportent {recovery:,.0f} EUR à la reprise.")
            else:
                safety_cost = wealth * 0.04
                wealth -= safety_cost
                stability += 6
                timeline.append(f"Branche prudente : protection de l'épargne, coût de {safety_cost:,.0f} EUR.")
            if accepts_work_change:
                wealth += 3500
                stability += 8
                timeline.append("Adaptation professionnelle : nouvelle source de revenus (+3,500 EUR).")
            else:
                stability -= 7
                timeline.append("Emploi inchangé : les revenus restent fragiles pendant la crise.")
        elif scenario_kind == "water_crisis":
            wealth -= wealth * 0.12
            stability -= 20
            timeline.append("Pénurie d'eau : hausse des dépenses et baisse de stabilité.")
            if accepts_protection:
                wealth -= 1800
                stability += 28
                timeline.append("Résilience : investissement dans l'eau ou le logement (-1,800 EUR, stabilité renforcée).")
            if accepts_migration:
                wealth -= 2200
                stability += 18
                timeline.append("Migration : coût de déplacement (-2,200 EUR), exposition au risque réduite.")
        else:
            wealth -= wealth * 0.10
            stability -= 12
            timeline.append("Choc initial : les ressources et la stabilité diminuent.")
            if accepts_protection or accepts_work_change or accepts_migration:
                wealth += 2200
                stability += 18
                timeline.append("Adaptation : une décision proactive améliore la situation finale.")
            else:
                stability -= 10
                timeline.append("Inaction : l'agent absorbe le choc sans levier d'adaptation.")

        wealth = round(max(0.0, wealth), 2)
        stability = round(max(0.0, min(100.0, stability)), 1)
        survival_threshold = (1500, 25) if scenario_kind == "apocalypse" else (1000, 20)
        survived = wealth >= survival_threshold[0] and stability >= survival_threshold[1]
        timeline.append(
            f"Fin : patrimoine {wealth:,.0f} EUR, stabilité {stability:.0f}/100, "
            f"statut {'survit' if survived else 'en difficulté critique'}."
        )
        outcomes.append(StoryOutcome(agent_id, wealth, stability, survived, timeline))

    ranking = sorted(outcomes, key=lambda outcome: (outcome.survived, outcome.wealth, outcome.stability), reverse=True)
    survivor_count = sum(outcome.survived for outcome in outcomes)
    return StorySimulation(
        scenario_kind,
        chapters_by_kind[scenario_kind],
        outcomes,
        ranking,
        survivor_count,
        len(outcomes) - survivor_count,
    )
