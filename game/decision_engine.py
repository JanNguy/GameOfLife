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
