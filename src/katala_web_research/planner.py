from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class SearchPlanStep:
    intent: str
    query: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_search_plan(query: str, *, max_subqueries: int = 4, year: int | None = None) -> list[SearchPlanStep]:
    cleaned = " ".join(query.split())
    if not cleaned:
        return []

    candidates = [
        SearchPlanStep("baseline", cleaned),
        SearchPlanStep("official", f"{cleaned} official docs documentation"),
        SearchPlanStep("primary", f"{cleaned} GitHub arxiv paper benchmark"),
        SearchPlanStep("critique", f"{cleaned} limitations evaluation source quality"),
    ]
    if year is not None and str(year) not in cleaned:
        candidates.append(SearchPlanStep("freshness", f"{cleaned} {year} latest changelog release notes"))

    seen: set[str] = set()
    plan: list[SearchPlanStep] = []
    for candidate in candidates:
        key = candidate.query.lower()
        if key in seen:
            continue
        seen.add(key)
        plan.append(candidate)
        if len(plan) >= max_subqueries:
            break
    return plan


def format_search_plan(plan: list[SearchPlanStep]) -> list[str]:
    return [f"{step.intent}: {step.query}" for step in plan]
