"""Deterministic accounting engine for a hypothetical federal fund.

Layer A / evidence grade A: identities only. No behavioral effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


TWOPLACES = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class FundParams:
    budget_brl: Decimal
    population_weight: Decimal
    need_weight: Decimal

    def normalized(self) -> FundParams:
        w_pop = self.population_weight
        w_need = self.need_weight
        total = w_pop + w_need
        if total <= 0:
            raise ValueError("population_weight + need_weight must be > 0")
        return FundParams(
            budget_brl=self.budget_brl,
            population_weight=w_pop / total,
            need_weight=w_need / total,
        )


def _q(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def distribute_hypothetical_fund(
    records: list[dict[str, Any]],
    params: FundParams,
    seed: int = 42,
) -> dict[str, Any]:
    """Distribute budget across UFs.

    share_i = w_pop * (pop_i / sum_pop) + w_need * (need_i / sum_need)
    amount_i = budget * share_i

    Remainder cents after rounding are assigned deterministically by descending
    fractional remainder, then UF code, so totals are conserved and reproducible.
    """
    _ = seed  # reserved for stochastic extensions; engine is deterministic
    p = params.normalized()
    if p.budget_brl < 0:
        raise ValueError("budget_brl must be >= 0")
    if len(records) != 27:
        raise ValueError("expected exactly 27 UF records")

    sum_pop = sum(Decimal(int(r["population"])) for r in records)
    sum_need = sum(Decimal(str(r["exploratory_need_index"])) for r in records)
    if sum_pop <= 0 or sum_need <= 0:
        raise ValueError("population and need totals must be > 0")

    raw_rows: list[dict[str, Any]] = []
    for r in records:
        pop = Decimal(int(r["population"]))
        need = Decimal(str(r["exploratory_need_index"]))
        pop_share = pop / sum_pop
        need_share = need / sum_need
        share = (p.population_weight * pop_share) + (p.need_weight * need_share)
        exact = p.budget_brl * share
        raw_rows.append(
            {
                "ibge_code": r["ibge_code"],
                "uf": r["uf"],
                "name": r["name"],
                "population": int(r["population"]),
                "need_index": float(r["exploratory_need_index"]),
                "share": share,
                "exact_amount": exact,
                "amount": _q(exact),
            }
        )

    allocated = sum((row["amount"] for row in raw_rows), ZERO)
    remainder = _q(p.budget_brl - allocated)
    cent = Decimal("0.01")
    # Adjust by +/- 1 cent until remainder is zero.
    ordered = sorted(
        raw_rows,
        key=lambda row: (
            -(row["exact_amount"] - row["amount"]),
            row["ibge_code"],
        ),
    )
    i = 0
    while remainder != ZERO and ordered:
        step = cent if remainder > 0 else -cent
        ordered[i % len(ordered)]["amount"] = _q(ordered[i % len(ordered)]["amount"] + step)
        remainder = _q(remainder - step)
        i += 1
        if i > 10_000:
            raise RuntimeError("failed to conserve budget within cent tolerance")

    allocations = []
    for row in sorted(raw_rows, key=lambda x: x["ibge_code"]):
        amount = row["amount"]
        per_capita = _q(amount / Decimal(row["population"]))
        allocations.append(
            {
                "ibge_code": row["ibge_code"],
                "uf": row["uf"],
                "name": row["name"],
                "population": row["population"],
                "need_index": row["need_index"],
                "share": f"{row['share']:.12f}",
                "amount_brl": f"{amount:.2f}",
                "per_capita_brl": f"{per_capita:.2f}",
                "status_label": "SIMULADO",
                "evidence_grade": "A",
            }
        )

    amounts = [Decimal(a["amount_brl"]) for a in allocations]
    total = sum(amounts, ZERO)
    shares = [Decimal(a["share"]) for a in allocations]
    herfindahl = sum((s * s for s in shares), ZERO)
    share_sum = sum(shares, ZERO)

    return {
        "budget_brl": f"{_q(p.budget_brl):.2f}",
        "population_weight": f"{p.population_weight:.12f}",
        "need_weight": f"{p.need_weight:.12f}",
        "total_allocated_brl": f"{_q(total):.2f}",
        "share_sum": f"{share_sum:.12f}",
        "concentration_hhi": f"{herfindahl:.12f}",
        "allocations": allocations,
        "invariants": {
            "n_ufs": len(allocations),
            "budget_conserved": _q(total) == _q(p.budget_brl),
            # Decimal string rounding of 27 shares can leave ~1e-12 residual.
            "shares_sum_to_one": abs(share_sum - ONE) < Decimal("1e-9"),
        },
    }
