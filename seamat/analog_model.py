"""Evidence-backed analogue transfer for user-defined materials.

The transfer is intentionally conservative.  It uses normalized ageing curves
only when a manually described material is sufficiently close to a catalogue
material that already has reviewed time-series evidence.  A similar Young's
modulus alone is never treated as proof of a similar ageing rate.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
import re
import unicodedata

import numpy as np

from seamat import material_db
from seamat.engine_v2 import Request, predict_from_evidence


ANALOG_VERSION = "seamat-analogue-transfer-1.0.0"
MIN_ANALOG_SCORE = 85


def _text(value: object) -> str:
    raw=unicodedata.normalize("NFKD",str(value or "").lower())
    return " ".join(re.findall(r"[a-z0-9]+","".join(c for c in raw if not unicodedata.combining(c))))


def _tokens(value: object) -> set[str]:
    return {token for token in _text(value).split() if len(token)>1}


def _mechanisms(material: dict) -> set[str]:
    return _tokens(material.get("mechanisms"))


def _candidate_modulus(material: dict, rows: list[dict]) -> float | None:
    profile=material_db.reference_property_profile(str(material.get("id") or ""))
    if profile and profile.get("representative_mpa"):
        return float(profile["representative_mpa"])
    starts=[]
    for row in rows:
        try:
            if float(row.get("time_days") or 0)==0:
                starts.append(float(row.get("modulus_mpa") or row.get("modulus_MPa")))
        except (TypeError,ValueError):
            continue
    return float(np.median(starts)) if starts else None


def _similarity(custom: dict, candidate: dict, rows: list[dict], exposure: str) -> dict:
    score=0.; reasons=[]; limits=[]
    custom_family=_text(custom.get("family") or custom.get("subcategory"))
    candidate_family=_text(candidate.get("family") or candidate.get("subcategory"))
    if custom_family and custom_family==candidate_family:
        score+=35; reasons.append("même famille chimique déclarée")
    elif _tokens(custom_family)&_tokens(candidate_family):
        score+=15; reasons.append("famille partiellement compatible")
    else:
        limits.append("famille chimique non concordante")

    identity=_tokens(" ".join(str(custom.get(key) or "") for key in
                              ("base_polymer","name","abbreviation","grade_reference")))
    candidate_identity=_tokens(" ".join(str(candidate.get(key) or "") for key in
                                        ("id","name","abbreviation","family","subtype")))
    identity_overlap=identity&candidate_identity
    if identity_overlap:
        score+=20; reasons.append("polymère de base concordant : "+", ".join(sorted(identity_overlap)))
    else:
        limits.append("polymère de base non confirmé")

    wanted=_mechanisms(custom); available=_mechanisms(candidate)
    if wanted and available:
        overlap=len(wanted&available)/len(wanted|available)
        score+=15*overlap
        if overlap>=.5: reasons.append("mécanismes de vieillissement proches")
        else: limits.append("mécanismes seulement partiellement couverts")
    else:
        limits.append("mécanismes insuffisamment décrits")

    custom_e0=float(custom.get("suggested_modulus_mpa") or 0)
    candidate_e0=_candidate_modulus(candidate,rows)
    modulus_ratio=None
    if custom_e0>0 and candidate_e0 and candidate_e0>0:
        modulus_ratio=custom_e0/candidate_e0
        modulus_points=max(0.,10*(1-abs(math.log(modulus_ratio))/math.log(4)))
        score+=modulus_points
        if .67<=modulus_ratio<=1.5: reasons.append("module initial du même ordre de grandeur")
        else: limits.append("module initial éloigné de l’analogue")

    row_text=_text(" ".join(str(row.get(key) or "") for row in rows
                            for key in ("protocol","formulation","medium")))
    process=_text(custom.get("process_state"))
    if process:
        common=_tokens(process)&_tokens(row_text)
        if common:
            score+=5; reasons.append("procédé ou état retrouvé dans le corpus")
        else:
            limits.append("procédé non confirmé par le corpus")
    else:
        limits.append("procédé non renseigné")

    reinforcement_pct=float(custom.get("reinforcement_pct") or 0)
    reinforcement=_text(custom.get("reinforcement"))
    if reinforcement_pct>0 or (reinforcement and reinforcement not in {"aucun","non charge"}):
        reinforcement_overlap=_tokens(reinforcement)&_tokens(row_text)
        if reinforcement_overlap and reinforcement_pct<=10:
            score+=5; reasons.append("renfort retrouvé dans les formulations sources")
        else:
            score-=20; limits.append("renfort ou charge absente des formulations sources")
    else:
        score+=5

    declared_exposure=str(custom.get("service_exposure") or "")
    if not declared_exposure or declared_exposure==exposure:
        score+=10
    else:
        score-=20; limits.append("milieu d’usage différent de la fiche personnalisée")

    score=int(round(max(0,min(100,score))))
    return {
        "material_id":candidate["id"],"material_name":candidate["name"],
        "score":score,"eligible":score>=MIN_ANALOG_SCORE,
        "reasons":reasons,"limits":limits,"evidence_rows":len(rows),
        "evidence_sources":len({str(row.get("source_id")) for row in rows}),
        "reference_modulus_mpa":candidate_e0,"modulus_ratio":modulus_ratio,
    }


def rank_analogs(custom: dict, exposure: str) -> list[dict]:
    """Rank only catalogue materials with reviewed evidence in the requested environment."""
    ranked=[]
    for candidate in material_db.catalog():
        rows=material_db.model_evidence_rows(candidate["id"],exposure)
        if not rows:
            continue
        ranked.append(_similarity(custom,candidate,rows,exposure))
    return sorted(ranked,key=lambda item:(-item["score"],item["material_name"]))


def predict_from_analogs(custom: dict, modulus_mpa: float, temperature_c: float,
                         humidity_rh: float, thickness_mm: float, horizon_days: float,
                         threshold_percent: float, exposure: str,
                         immersion_medium: str | None = None,
                         grade_reference: str | None = None,
                         process_state: str | None = None) -> dict | None:
    """Return a qualified analogue transfer, or ``None`` when similarity is inadequate."""
    enriched=dict(custom)
    if grade_reference: enriched["grade_reference"]=grade_reference
    if process_state: enriched["process_state"]=process_state
    candidates=rank_analogs(enriched,exposure)
    if not candidates or not candidates[0]["eligible"]:
        return None
    best=candidates[0]
    rows=material_db.model_evidence_rows(best["material_id"],exposure)
    if exposure=="immersion":
        wanted={"milform64":"milform 64 sst","Milform 64 SST":"milform 64 sst"}.get(immersion_medium)
        rows=[row for row in rows if wanted and wanted in str(row.get("medium","")).lower()]
    if not rows:
        return None
    routed=predict_from_evidence(Request(
        material_id=str(custom.get("id") or "CUSTOM"),
        material_name=str(custom.get("name") or "Matériau personnalisé"),
        modulus_mpa=float(modulus_mpa),temperature_c=float(temperature_c),
        humidity_rh=float(humidity_rh),thickness_mm=float(thickness_mm),
        horizon_days=float(horizon_days),threshold_percent=float(threshold_percent),
        exposure=exposure,immersion_medium=immersion_medium,
        # The custom grade label must not be used as a substring filter on the
        # analogue corpus ("PP" would otherwise mix unrelated PP studies).
        grade_reference=None,process_state=None,
    ),rows)
    if routed is None:
        return None

    manifest=routed["manifest"]; assumptions=manifest["assumptions"]
    source_uncertainty=dict(manifest.get("uncertainty") or {})
    base_half=math.log1p(float(source_uncertainty.get("base_half_width_pct") or 2.5)/100)
    transfer_half=.08+(100-best["score"])/100*.45
    total_half=math.sqrt(base_half**2+transfer_half**2)
    center=np.asarray(routed["modulus"],dtype=float)
    routed["lower"]=(center*np.exp(-total_half)).tolist()
    routed["upper"]=(center*np.exp(total_half)).tolist()
    crossing=routed.get("crossing_estimate_years")
    evidence_window_years=float(assumptions.get("evidence_window_days") or 0)/365.25
    threshold_within_evidence=bool(crossing is not None and crossing<=evidence_window_years+1e-12)
    speed_delta=min(.55,.12+(100-best["score"])/100)
    crossing_interval=([
        float(crossing)/(1+speed_delta),float(crossing)/(1-speed_delta)
    ] if crossing is not None else [None,None])
    assumptions["analog_transfer"]={
        "version":ANALOG_VERSION,"source_material_id":best["material_id"],
        "source_material_name":best["material_name"],"similarity_score":best["score"],
        "minimum_score":MIN_ANALOG_SCORE,"reasons":best["reasons"],"limits":best["limits"],
        "alternatives":[{key:value for key,value in item.items() if key not in {"reasons","limits"}}
                        for item in candidates[:3]],
        "transfer_half_width_pct":float((math.exp(transfer_half)-1)*100),
        "threshold_within_evidence":threshold_within_evidence,
    }
    if not threshold_within_evidence:
        assumptions["analog_transfer"]["unqualified_threshold_projection_years"]=crossing
        routed["crossing_estimate_years"]=None
        routed["crossing_interval"]=[None,None]
        routed["crossing"]=None
        routed["fraction_crossing"]=0.
    else:
        routed["crossing_interval"]=crossing_interval
    manifest["model"]="datasheet-analog-transfer-v1"
    manifest["engine_version"]=ANALOG_VERSION
    manifest["dataset"]="verified-literature-analogue-transfer"
    manifest["evidence_level"]="analogue_supported_screening"
    manifest["validity"]["material_scope"]=(
        f"Transfert de {best['material_name']} vers {custom.get('name','matériau personnalisé')} ; "
        f"similarité documentaire {best['score']}/100")
    manifest["uncertainty"]={
        "kind":"source_calibration_plus_analogue_penalty",
        "label":f"Bande source + pénalité de transfert ({best['score']}/100)",
        "coverage":"niveau cible de la source, couverture du transfert non démontrée",
        "interpretation":"Combinaison quadratique de l’erreur de la source et d’une pénalité liée à la similarité.",
        "predictive_interval_validated":False,"display_band":True,
        "base_half_width_pct":float((math.exp(total_half)-1)*100),
        "source_specific":source_uncertainty,
        "excludes":["effet inconnu des additifs","variabilité du grade personnalisé","changement de mécanisme"],
    }
    manifest["warnings"].insert(0,
        f"Aucune série propre au matériau : cinétique transférée depuis {best['material_name']} ({best['score']}/100).")
    manifest["status"]="ESTIMATION PAR ANALOGUE DOCUMENTÉ · DOMAINE LIMITÉ"
    routed["fingerprint"]=sha256(json.dumps(manifest,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return routed
