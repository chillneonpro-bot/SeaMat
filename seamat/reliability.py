"""Universal scientific qualification gates for SeaMat results.

Every material is evaluated with the same rules.  The gate never turns a
documentary family curve into a validated prediction: it decides which use is
allowed from the evidence, the hidden-group errors and the requested domain.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Any


GATE_VERSION = "seamat-reliability-gate-1.0.0"
MIN_HIDDEN_PREDICTIONS = 6
MAX_MAPE_PCT = 10.0
MAX_APE_PCT = 20.0
MIN_COVERAGE_PCT = 80.0
MAX_COVERAGE_PCT = 100.0
MIN_EXTERNAL_SOURCES = 2


@dataclass(frozen=True)
class ReliabilityDecision:
    code: str
    label: str
    tone: str
    usable_for_screening: bool
    qualified_external: bool
    decision: str
    scope: str
    reasons: list[str]
    next_actions: list[str]


def _number(value: Any) -> float | None:
    try:
        number=float(value)
        return number if number==number else None
    except (TypeError,ValueError):
        return None


def _criteria(validation: dict) -> dict:
    predictions=int(validation.get("test_predictions") or 0)
    mape=_number(validation.get("mape_pct"))
    maximum=_number(validation.get("max_ape_pct"))
    coverage=_number(validation.get("empirical_point_coverage_pct"))
    checks={
        "hidden_predictions":predictions>=MIN_HIDDEN_PREDICTIONS,
        "mape":mape is not None and mape<=MAX_MAPE_PCT,
        "maximum_error":maximum is not None and maximum<=MAX_APE_PCT,
        "coverage":coverage is not None and MIN_COVERAGE_PCT<=coverage<=MAX_COVERAGE_PCT,
    }
    return {
        "thresholds":{"minimum_hidden_predictions":MIN_HIDDEN_PREDICTIONS,
                      "maximum_mape_pct":MAX_MAPE_PCT,"maximum_ape_pct":MAX_APE_PCT,
                      "coverage_range_pct":[MIN_COVERAGE_PCT,MAX_COVERAGE_PCT]},
        "observed":{"hidden_predictions":predictions,"mape_pct":mape,
                    "max_ape_pct":maximum,"coverage_pct":coverage},
        "checks":checks,"passed":all(checks.values()),
    }


def assess_result(result: dict) -> dict:
    """Classify a result with one rule set shared by every material."""
    manifest=result.get("manifest") or {}
    assumptions=manifest.get("assumptions") or {}
    model=str(manifest.get("model") or "")
    validation=assumptions.get("validation") or {}
    criteria=_criteria(validation)
    multiple=_number(assumptions.get("extrapolation_multiple"))
    in_time_domain=multiple is not None and multiple<=1.0+1e-9
    route=str(assumptions.get("profile_method") or "documentary_family")
    sources=int(assumptions.get("independent_sources") or 0)
    match=(assumptions.get("documentary_match") or {})
    match_score=int(match.get("score") or 0)
    engine_backed=model=="datasheet-screening-v6-seamat-engine"

    if not engine_backed:
        decision=ReliabilityDecision(
            code="documentary_only",label="Non qualifié · données de vieillissement absentes",tone="red",
            usable_for_screening=False,qualified_external=False,
            decision="La courbe est un scénario documentaire. Aucune durée de vie exploitable ne doit en être déduite.",
            scope="Comparaison pédagogique des hypothèses uniquement.",
            reasons=["aucune série temporelle compatible et acceptée","cinétique transférée depuis une famille"],
            next_actions=["ajouter au moins trois séries comparables et douze points",
                          "réserver une campagne ou une publication indépendante à la validation"],
        )
    elif not in_time_domain:
        decision=ReliabilityDecision(
            code="extrapolation_unqualified",label="Non qualifié · hors fenêtre publiée",tone="red",
            usable_for_screening=False,qualified_external=False,
            decision="La courbe dépasse la dernière observation compatible ; le temps au seuil reste une hypothèse.",
            scope=f"Interpolation autorisée jusqu’à {float(assumptions.get('evidence_window_days') or 0):g} jours.",
            reasons=[f"horizon ×{multiple:.2f} la fenêtre observée" if multiple is not None else "horizon non contrôlé"],
            next_actions=["réduire l’horizon à la fenêtre publiée","ajouter des observations plus longues"],
        )
    elif route=="exact_temperature_curve" and not criteria["passed"]:
        decision=ReliabilityDecision(
            code="published_exact_unvalidated",label="Profil publié exact · validation limitée",tone="amber",
            usable_for_screening=True,qualified_external=False,
            decision="La courbe décrit les conditions publiées exactes, mais sa capacité prédictive indépendante n’est pas démontrée.",
            scope="Lecture et interpolation dans la fenêtre et aux conditions exactes.",
            reasons=["pas assez de groupes indépendants masquables"],
            next_actions=["ajouter une campagne indépendante aux mêmes conditions"],
        )
    elif not criteria["passed"]:
        failed=[name for name,passed in criteria["checks"].items() if not passed]
        decision=ReliabilityDecision(
            code="validation_failed",label="Non qualifié · validation insuffisante",tone="red",
            usable_for_screening=False,qualified_external=False,
            decision="Les erreurs sur données masquées dépassent les critères communs de SeaMat.",
            scope="Analyse de sensibilité et préparation d’une nouvelle campagne seulement.",
            reasons=["critères échoués : "+", ".join(failed)],
            next_actions=["ajouter des groupes indépendants","revoir la route ou le mécanisme physique"],
        )
    elif sources>=MIN_EXTERNAL_SOURCES and match_score>=80:
        decision=ReliabilityDecision(
            code="externally_supported",label="Fiabilité démontrée dans le domaine publié",tone="teal",
            usable_for_screening=True,qualified_external=True,
            decision="Les critères d’erreur, de couverture, de correspondance et d’indépendance des sources sont satisfaits.",
            scope="Présélection dans le domaine documenté ; qualification de sécurité toujours exclue.",
            reasons=[f"{criteria['observed']['hidden_predictions']} prédictions masquées",
                     f"{sources} sources indépendantes",f"correspondance {match_score}/100"],
            next_actions=["maintenir un jeu externe gelé à chaque nouvelle version"],
        )
    else:
        decision=ReliabilityDecision(
            code="internally_supported",label="Fiabilité interne · domaine publié",tone="teal",
            usable_for_screening=True,qualified_external=False,
            decision="Les erreurs internes sont faibles, mais la preuve indépendante reste insuffisante.",
            scope="Présélection de recherche dans la fenêtre et pour un grade/protocole comparable.",
            reasons=[f"{criteria['observed']['hidden_predictions']} prédictions masquées",
                     f"{sources} source(s) utilisée(s)",f"correspondance {match_score}/100"],
            next_actions=["valider sur une publication, un grade ou un laboratoire entièrement indépendant"],
        )
    payload=asdict(decision)
    payload.update({"gate_version":GATE_VERSION,"criteria":criteria,
                    "route":route,"match_score":match_score,"source_count":sources,
                    "within_published_time":in_time_domain})
    return payload


def apply_reliability_gate(result: dict) -> dict:
    manifest=result.setdefault("manifest",{})
    original=manifest.get("status")
    assessment=assess_result(result)
    assessment["model_status"]=original
    manifest["reliability"]=assessment
    manifest["status"]=assessment["label"].upper()
    uncertainty=manifest.get("uncertainty") or {}
    uncertainty["qualified_for_use"]=bool(assessment["usable_for_screening"])
    if not assessment["usable_for_screening"]:
        original_label=str(uncertainty.get("label") or "Plage du modèle")
        uncertainty["label"]="Plage non qualifiée · "+original_label
        uncertainty["predictive_interval_validated"]=False
    result["fingerprint"]=sha256(json.dumps(manifest,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return result


def material_coverage(material: dict, rows: list[dict]) -> dict:
    """Describe the shortest path from a catalogue card to an eligible model."""
    from seamat.engine_v2 import evidence_quality
    audit=evidence_quality(rows)
    points=int(audit["rows_valid"]); experiments=int(audit["usable_experiments"])
    sources=int(audit["independent_sources"])
    if experiments>=3 and points>=12 and sources>=2:
        code="benchmark_ready"; label="Corpus prêt pour validation"
    elif experiments>=1:
        code="evidence_limited"; label="Corpus scientifique limité"
    else:
        code="documentary_only"; label="Fiche documentaire uniquement"
    return {
        "material_id":material["id"],"material_name":material["name"],
        "coverage_code":code,"coverage_label":label,
        "rows":points,"experiments":experiments,"sources":sources,
        "missing":{"rows":max(0,12-points),"experiments":max(0,3-experiments),
                   "sources":max(0,2-sources)},
        "can_attempt_calibration":experiments>=3 and points>=12,
        "can_claim_external_reliability":False,
        "next_action":("Lancer la validation par groupes et réserver une source externe."
                       if code=="benchmark_ready" else
                       "Compléter les séries temporelles, les conditions et les sources indépendantes."),
    }
