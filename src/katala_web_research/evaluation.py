from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import SearchResult
from .planner import build_search_plan
from .rank import rank_results
from .source_quality import classify_url


@dataclass(slots=True, frozen=True)
class EvalCase:
    name: str
    query: str
    candidates: list[SearchResult]
    expected_plan_intents: tuple[str, ...]
    preferred_url_terms: tuple[str, ...]
    discouraged_url_terms: tuple[str, ...] = ()
    min_top_quality: int = 75


@dataclass(slots=True)
class EvalCaseResult:
    name: str
    query: str
    score: int
    passed: bool
    plan_intents: list[str]
    top_urls: list[str]
    metrics: dict[str, int | bool]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class EvalSummary:
    score: int
    passed: bool
    min_score: int
    cases: list[EvalCaseResult]

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "passed": self.passed,
            "min_score": self.min_score,
            "cases": [case.to_dict() for case in self.cases],
        }


def default_eval_cases() -> list[EvalCase]:
    return [
        EvalCase(
            name="agentic_retrieval_prefers_official_and_primary",
            query="agentic retrieval source quality",
            candidates=[
                SearchResult(
                    title="Agentic retrieval: a practical guide",
                    url="https://www.algolia.com/blog/ai/agentic-retrieval",
                    snippet="Agentic retrieval amplifies existing data quality issues.",
                    rank=1,
                ),
                SearchResult(
                    title="Agentic Retrieval Overview - Azure AI Search",
                    url="https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview",
                    snippet="A pipeline that decomposes complex queries into subqueries for agent workflows.",
                    rank=2,
                ),
                SearchResult(
                    title="Agentic retrieval in Azure AI Search",
                    url="https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/search/agentic-retrieval-overview.md",
                    snippet="Primary documentation source for agentic retrieval behavior.",
                    rank=3,
                ),
            ],
            expected_plan_intents=("baseline", "official", "primary"),
            preferred_url_terms=("learn.microsoft.com", "github.com/MicrosoftDocs"),
            discouraged_url_terms=("algolia.com/blog",),
        ),
        EvalCase(
            name="citations_prefers_vendor_docs",
            query="Claude citations source documents",
            candidates=[
                SearchResult(
                    title="How to add citations to an AI app",
                    url="https://example.com/claude-citations-guide",
                    snippet="A blog tutorial about citations.",
                    rank=1,
                ),
                SearchResult(
                    title="Citations - Anthropic",
                    url="https://docs.anthropic.com/en/docs/build-with-claude/citations",
                    snippet="Citations provide source locations for generated responses.",
                    rank=2,
                ),
            ],
            expected_plan_intents=("baseline", "official"),
            preferred_url_terms=("docs.anthropic.com",),
            discouraged_url_terms=("example.com",),
        ),
        EvalCase(
            name="papers_surface_primary_research",
            query="query decomposition retrieval augmented generation evaluation",
            candidates=[
                SearchResult(
                    title="Query decomposition for RAG",
                    url="https://arxiv.org/abs/2510.18633",
                    snippet="Retrieval-augmented generation systems decompose requests into subqueries.",
                    rank=2,
                    published_at="2025-10-22",
                ),
                SearchResult(
                    title="Advanced RAG production patterns",
                    url="https://example.com/advanced-rag-patterns",
                    snippet="A high-level production guide.",
                    rank=1,
                ),
                SearchResult(
                    title="Question Decomposition for Retrieval-Augmented Generation",
                    url="https://aclanthology.org/2025.acl-srw.32/",
                    snippet="A RAG pipeline that incorporates question decomposition and reranking.",
                    rank=3,
                    published_at="2025-07-01",
                ),
            ],
            expected_plan_intents=("baseline", "primary", "critique"),
            preferred_url_terms=("arxiv.org", "aclanthology.org"),
            discouraged_url_terms=("example.com",),
        ),
        EvalCase(
            name="fusion_consensus_beats_single_engine_outlier",
            query="agent search documentation rank fusion",
            candidates=[
                SearchResult(
                    title="Generic search notes",
                    url="https://example.com/rank-fusion",
                    snippet="A single-engine blog result.",
                    rank=1,
                ),
                SearchResult(
                    title="Agent search rank fusion documentation",
                    url="https://docs.github.com/en/search-github",
                    snippet="Official documentation for searching GitHub.",
                    rank=2,
                    metadata={"rrf_score": 0.031, "source_count": 2},
                ),
            ],
            expected_plan_intents=("baseline", "official", "primary"),
            preferred_url_terms=("docs.github.com",),
            discouraged_url_terms=("example.com",),
        ),
    ]


def run_eval(*, min_score: int = 80, max_subqueries: int = 4) -> EvalSummary:
    results = [evaluate_case(case, max_subqueries=max_subqueries) for case in default_eval_cases()]
    score = round(sum(result.score for result in results) / max(len(results), 1))
    return EvalSummary(score=score, passed=score >= min_score, min_score=min_score, cases=results)


def evaluate_case(case: EvalCase, *, max_subqueries: int = 4) -> EvalCaseResult:
    plan = build_search_plan(case.query, max_subqueries=max_subqueries)
    ranked = rank_results(case.query, list(case.candidates))
    top_urls = [result.url for result in ranked[:3]]
    top_quality = classify_url(top_urls[0])[1] if top_urls else 0

    plan_intents = [step.intent for step in plan]
    intent_hits = sum(1 for intent in case.expected_plan_intents if intent in plan_intents)
    preferred_hits = sum(1 for term in case.preferred_url_terms if any(term in url for url in top_urls[:2]))
    discouraged_above_preferred = _discouraged_above_preferred(case, top_urls)
    quality_ok = top_quality >= case.min_top_quality

    score = 0
    score += round(30 * intent_hits / max(len(case.expected_plan_intents), 1))
    score += round(40 * preferred_hits / max(len(case.preferred_url_terms), 1))
    score += 20 if quality_ok else 0
    score += 10 if not discouraged_above_preferred else 0

    return EvalCaseResult(
        name=case.name,
        query=case.query,
        score=score,
        passed=score >= 80,
        plan_intents=plan_intents,
        top_urls=top_urls,
        metrics={
            "intent_hits": intent_hits,
            "preferred_hits": preferred_hits,
            "quality_ok": quality_ok,
            "discouraged_above_preferred": discouraged_above_preferred,
        },
    )


def build_eval_report(summary: EvalSummary) -> str:
    lines = [
        "# Research Quality Benchmark",
        "",
        f"- score: {summary.score}",
        f"- min_score: {summary.min_score}",
        f"- passed: {str(summary.passed).lower()}",
        f"- cases: {len(summary.cases)}",
        "",
        "## Cases",
        "",
    ]
    for case in summary.cases:
        lines.extend(
            [
                f"### {case.name}",
                "",
                f"- query: {case.query}",
                f"- score: {case.score}",
                f"- passed: {str(case.passed).lower()}",
                f"- plan_intents: {', '.join(case.plan_intents)}",
                f"- top_urls: {', '.join(case.top_urls)}",
                f"- metrics: {case.metrics}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _discouraged_above_preferred(case: EvalCase, top_urls: list[str]) -> bool:
    first_preferred = _first_index(top_urls, case.preferred_url_terms)
    first_discouraged = _first_index(top_urls, case.discouraged_url_terms)
    return first_discouraged is not None and (first_preferred is None or first_discouraged < first_preferred)


def _first_index(urls: list[str], terms: tuple[str, ...]) -> int | None:
    for idx, url in enumerate(urls):
        if any(term in url for term in terms):
            return idx
    return None
