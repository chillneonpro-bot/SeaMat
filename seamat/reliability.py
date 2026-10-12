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
from scipy.stats import beta


GATE_VERSION = "seamat-reliability-gate-1.1.0"
MIN_HIDDEN_PREDICTIONS = 6
MAX_MAPE_PCT = 10.0
MAX_APE_PCT = 20.0
MIN_COVERAGE_PCT = 80.0
MAX_COVERAGE_PCT = 100.0
MIN_EXTERNAL_SOURCES = 2
TARGET_RELIABILITY_PCT = 95.0
TARGET_CONFIDENCE_PCT = 95.0


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


def _coverage_95_claim(validation: dict, sources: int) -> dict:
    """One-sided exact binomial audit for a 95 % coverage claim.

    Whole hidden formulations/temperatures are the statistical units whenever
    the engine exposes them.  A group passes only if all its hidden points are
    covered, preventing many correlated time points from inflating confidence.
    """
    point_count=int(validation.get("test_predictions") or 0)
    groups=int(validation.get("independent_validation_groups") or 0)
    covered_groups=int(validation.get("covered_validation_groups") or 0)
    if groups<=0:
        coverage=_number(validation.get("empirical_point_coverage_pct"))
        groups=point_count
        covered_groups=(int(round(groups*(coverage or 0)/100)) if coverage is not None else 0)
    if groups<=0 or covered_groups<=0:
        lower=0.
    else:
        lower=float(beta.ppf(1-TARGET_CONFIDENCE_PCT/100,covered_groups,groups-covered_groups+1)*100)
    # Best-case number of additional fully covered, independent groups needed
    # from the current result. This is 59 total groups when there are no misses.
    required_total=None
    for total in range(groups,10001):
        successes=covered_groups+(total-groups)
        bound=(float(beta.ppf(.05,successes,total-successes+1)*100) if successes else 0.)
        if bound>=TARGET_RELIABILITY_PCT:
            required_total=total; break
    qualified=bool(lower>=TARGET_RELIABILITY_PCT and sources>=MIN_EXTERNAL_SOURCES)
    return {
        "target_coverage_pct":TARGET_RELIABILITY_PCT,
        "confidence_level_pct":TARGET_CONFIDENCE_PCT,
        "validation_unit":"groupe indépendant entièrement masqué",
        "independent_groups":groups,"covered_groups":covered_groups,
        "observed_group_coverage_pct":float(covered_groups/groups*100) if groups else None,
        "one_sided_lower_bound_pct":lower,
        "minimum_external_sources":MIN_EXTERNAL_SOURCES,"observed_sources":sources,
        "required_total_groups_best_case":required_total,
        "additional_groups_best_case":(required_total-groups if required_total is not None else None),
        "qualified":qualified,
        "decision":("Objectif 95/95 démontré dans le domaine testé."
                    if qualified else
                    "Objectif 95/95 non démontré : la précision observée ne suffit pas sans assez de groupes externes."),
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
    claim_95=_coverage_95_claim(validation,sources)
    match=(assumptions.get("documentary_match") or {})
    match_score=int(match.get("score") or 0)
    engine_backed=model=="datasheet-screening-v6-seamat-engine"
    analog=assumptions.get("analog_transfer") or {}

    if analog:
        analog_score=int(analog.get("similarity_score") or 0)
        analog_minimum=int(analog.get("minimum_score") or 85)
        if not in_time_domain:
            decision=ReliabilityDecision(
                code="analog_extrapolation_unqualified",label="Analogue proche · hors fenêtre publiée",tone="red",
                usable_for_screening=False,qualified_external=False,
                decision="L’analogue est suffisamment proche, mais l’horizon dépasse les observations qui fondent le transfert.",
                scope=f"Usage limité à {float(assumptions.get('evidence_window_days') or 0):g} jours.",
                reasons=[f"similarité {analog_score}/100",f"horizon ×{multiple:.2f} la fenêtre observée"],
                next_actions=["réduire l’horizon","ajouter une source analogue couvrant une durée plus longue"],
            )
        elif analog_score<analog_minimum or not criteria["passed"]:
            failed=[name for name,passed in criteria["checks"].items() if not passed]
            decision=ReliabilityDecision(
                code="analog_unqualified",label="Analogue insuffisant · estimation non qualifiée",tone="red",
                usable_for_screening=False,qualified_external=False,
                decision="La proximité de l’analogue ou sa validation ne suffit pas pour rendre ce calcul exploitable.",
                scope="Hypothèse de recherche uniquement.",
                reasons=[f"similarité {analog_score}/100, seuil {analog_minimum}/100"]+
                        (["critères échoués : "+", ".join(failed)] if failed else []),
                next_actions=["compléter la formulation et le procédé","choisir un analogue documenté plus proche"],
            )
        else:
            decision=ReliabilityDecision(
                code="analog_supported_limited",label="Analogue documenté · usage limité",tone="teal",
                usable_for_screening=True,qualified_external=False,
                decision="La valeur centrale est exploitable pour une présélection dans la fenêtre publiée de l’analogue.",
                scope="Comparaison et présélection de recherche ; le grade personnalisé n’est pas qualifié.",
                reasons=[f"similarité {analog_score}/100",
                         f"{criteria['observed']['hidden_predictions']} prédictions masquées sur l’analogue",
                         f"transfert depuis {analog.get('source_material_name','un matériau publié')}"] ,
                next_actions=["conserver la fiche exacte du grade","valider ultérieurement sur un jeu indépendant"],
            )
    elif not engine_backed:
        analog_search=assumptions.get("analog_search") or {}
        best_analog=analog_search.get("best") or {}
        documentary_reasons=["aucune série temporelle compatible et acceptée","cinétique transférée depuis une famille"]
        documentary_actions=["ajouter au moins trois séries comparables et douze points",
                             "réserver une campagne ou une publication indépendante à la validation"]
        if analog_search:
            documentary_reasons=[
                (f"meilleur analogue : {best_analog.get('material_name')} à {best_analog.get('score',0)}/100, "
                 f"sous le seuil {analog_search.get('minimum_score',85)}/100")
                if best_analog else "aucun analogue publié dans le milieu demandé",
            ]+(best_analog.get("limits") or [])
            documentary_actions=["compléter le polymère de base, la formulation, le procédé et les additifs",
                                 "ajouter un analogue publié compatible au corpus"]
        decision=ReliabilityDecision(
            code="documentary_only",label="Non qualifié · données de vieillissement absentes",tone="red",
            usable_for_screening=False,qualified_external=False,
            decision="La courbe est un scénario documentaire. Aucune durée de vie exploitable ne doit en être déduite.",
            scope="Comparaison pédagogique des hypothèses uniquement.",
            reasons=documentary_reasons,
            next_actions=documentary_actions,
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
    elif claim_95["qualified"] and match_score>=80:
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
                    "within_published_time":in_time_domain,
                    "analog_score":int(analog.get("similarity_score") or 0) if analog else None,
                    "reliability_95":claim_95})
    return payload


def apply_reliability_gate(result: dict) -> dict:
    manifest=result.setdefault("manifest",{})
    original=manifest.get("status")
    assessment=assess_result(result)
    assessment["model_status"]=original
    manifest["reliability"]=assessment
    manifest["reliability_95"]=assessment["reliability_95"]
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
