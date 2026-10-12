"""Evidence-routed prediction engine for SeaMat V2.

The engine deliberately separates interpolation, kinetic extrapolation and
family transfer.  It never uses a requested point to validate itself: model
errors and predictive bands are estimated from held-out experiments or held-
out temperatures whenever the corpus permits it.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import warnings
from typing import Callable

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import curve_fit
from scipy.optimize import OptimizeWarning
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


ENGINE_VERSION = "seamat-evidence-router-2.1.0"
TARGET_COVERAGE = 0.90
MIN_RETENTION = 1e-6


@dataclass(frozen=True)
class Request:
    material_id: str
    material_name: str
    modulus_mpa: float
    temperature_c: float
    humidity_rh: float
    thickness_mm: float
    horizon_days: float
    threshold_percent: float
    exposure: str
    immersion_medium: str | None = None
    grade_reference: str | None = None
    process_state: str | None = None


def _finite(value: object) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _canonical_row(row: dict) -> dict:
    """Normalize published and institution-reviewed rows to one schema."""
    canonical=dict(row)
    if canonical.get("time_days") is None and _finite(canonical.get("time_hours")):
        canonical["time_days"]=float(canonical["time_hours"])/24
    canonical["modulus_mpa"]=(canonical.get("modulus_mpa")
                              if canonical.get("modulus_mpa") is not None
                              else canonical.get("modulus_MPa"))
    canonical["standard_deviation_mpa"]=(canonical.get("standard_deviation_mpa")
                                          if canonical.get("standard_deviation_mpa") is not None
                                          else canonical.get("sd_mpa"))
    canonical["ageing_temperature_c"]=(canonical.get("ageing_temperature_c")
                                        if canonical.get("ageing_temperature_c") is not None
                                        else canonical.get("temperature_C"))
    canonical["humidity_rh"]=(canonical.get("humidity_rh")
                              if canonical.get("humidity_rh") is not None
                              else canonical.get("humidity_RH"))
    if canonical.get("evidence_status") is None and canonical.get("review_status")=="accepted":
        canonical["evidence_status"]="accepted_scientific_review"
    canonical.setdefault("property_name","Module de Young en traction")
    return canonical


def validate_request(request: Request) -> None:
    values=(request.modulus_mpa,request.temperature_c,request.humidity_rh,
            request.thickness_mm,request.horizon_days,request.threshold_percent)
    if not all(_finite(value) for value in values):
        raise ValueError("Les entrées du moteur V2 doivent être numériques et finies.")
    if request.modulus_mpa<=0 or request.thickness_mm<=0 or request.horizon_days<=0:
        raise ValueError("Module, épaisseur et horizon doivent être strictement positifs.")
    if not -40<=request.temperature_c<=160 or not 0<=request.humidity_rh<=100:
        raise ValueError("Température ou humidité hors du domaine SeaMat.")
    if not 1<=request.threshold_percent<=100:
        raise ValueError("Le seuil doit être compris entre 1 et 100 %.")
    if request.exposure not in {"indoor","outdoor","immersion"}:
        raise ValueError("Milieu d’exposition inconnu.")


def evidence_quality(rows: list[dict]) -> dict:
    """Audit the scientific data contract before any numerical fit."""
    issues=[]; valid=[]
    seen=set()
    for index,original in enumerate(rows):
        row=_canonical_row(original)
        required=("experiment_id","time_days","modulus_mpa","source_id")
        missing=[name for name in required if row.get(name) in {None,""}]
        if missing:
            issues.append(f"Ligne {index+1} : champs manquants {', '.join(missing)}")
            continue
        if not _finite(row["time_days"]) or not _finite(row["modulus_mpa"]):
            issues.append(f"Ligne {index+1} : temps ou module non numérique")
            continue
        time=float(row["time_days"]); modulus=float(row["modulus_mpa"])
        if time<0 or modulus<=0:
            issues.append(f"Ligne {index+1} : temps négatif ou module non positif")
            continue
        key=(str(row["source_id"]),str(row["experiment_id"]),time)
        if key in seen:
            issues.append(f"Doublon : {key[0]} / {key[1]} / {time:g} j")
            continue
        seen.add(key); valid.append(row)
    experiments=sorted({str(row["experiment_id"]) for row in valid})
    sources=sorted({str(row["source_id"]) for row in valid})
    t0_experiments=[]; usable=[]
    for experiment in experiments:
        group=[row for row in valid if str(row["experiment_id"])==experiment]
        times={float(row["time_days"]) for row in group}
        if 0.0 in times:
            t0_experiments.append(experiment)
        if len(times)>=3 and 0.0 in times:
            usable.append(experiment)
    property_compatible=sum(
        not row.get("property_name") or "module de young" in str(row["property_name"]).lower()
        for row in valid
    )
    score=100
    score-=min(35,5*len(issues))
    if valid and property_compatible<len(valid): score-=25
    if experiments and len(t0_experiments)<len(experiments): score-=20
    if len(usable)<1: score-=40
    return {
        "score":max(0,score),"rows_received":len(rows),"rows_valid":len(valid),
        "experiments":len(experiments),"usable_experiments":len(usable),
        "independent_sources":len(sources),"source_ids":sources,
        "issues":issues,"valid_rows":valid,
        "status":"usable" if usable else "insufficient",
    }


def _series(rows: list[dict]) -> list[dict]:
    result=[]
    for experiment_id in sorted({str(row["experiment_id"]) for row in rows}):
        group=sorted((row for row in rows if str(row["experiment_id"])==experiment_id),
                     key=lambda row:float(row["time_days"]))
        if len(group)<3 or not np.isclose(float(group[0]["time_days"]),0):
            continue
        times=np.asarray([float(row["time_days"]) for row in group],dtype=float)
        values=np.asarray([float(row["modulus_mpa"]) for row in group],dtype=float)
        if np.any(values<=0) or len(np.unique(times))!=len(times):
            continue
        e0=float(values[0]); retention=values/e0
        sd=np.asarray([float(row.get("standard_deviation_mpa") or 0)/e0 for row in group])
        se=np.asarray([float(row.get("standard_deviation_mpa") or 0)/e0/
                       math.sqrt(max(float(row.get("sample_count") or 1),1)) for row in group])
        increases=np.diff(retention)>max(.02,.03*float(np.median(retention)))
        result.append({
            "id":experiment_id,"source_id":str(group[0].get("source_id") or "source-inconnue"),
            "times":times,"retention":retention,"sd":sd,"se":se,"rows":group,"e0":e0,
            "temperature_c":(float(group[0]["ageing_temperature_c"])
                               if group[0].get("ageing_temperature_c") is not None else None),
            "medium":group[0].get("medium"),"formulation":group[0].get("formulation"),
            "non_monotonic":bool(np.any(increases)),
        })
    return result


def _exp_model(time: np.ndarray, rate: float) -> np.ndarray:
    return np.exp(-rate*np.asarray(time,dtype=float))


def _weibull_model(time: np.ndarray, tau: float, beta: float) -> np.ndarray:
    return np.exp(-np.power(np.maximum(np.asarray(time,dtype=float),0)/tau,beta))


def _plateau_model(time: np.ndarray, rate: float, plateau: float) -> np.ndarray:
    return plateau+(1-plateau)*np.exp(-rate*np.asarray(time,dtype=float))


def _fit_candidate(name: str, times: np.ndarray, values: np.ndarray) -> tuple[Callable[[np.ndarray],np.ndarray],dict]:
    positive=times>0; x=times[positive]; y=np.clip(values[positive],MIN_RETENTION,2.)
    max_time=max(float(times[-1]),1e-6)
    if name=="exponential":
        loss=np.maximum(-np.log(np.minimum(y,1.)),0)
        rate=float(np.dot(x,loss)/max(np.dot(x,x),1e-12))
        return lambda t:_exp_model(np.asarray(t),rate),{"rate_per_day":rate,"parameters":1}
    if name=="weibull":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore",OptimizeWarning)
            params,_=curve_fit(_weibull_model,x,np.minimum(y,1.),p0=(max_time,1.),
                               bounds=([max_time/1000,.2],[max_time*1000,4.]),maxfev=20000)
        tau,beta=map(float,params)
        return lambda t:_weibull_model(np.asarray(t),tau,beta),{"tau_days":tau,"beta":beta,"parameters":2}
    if name=="plateau_exponential":
        upper_plateau=min(.99,float(np.min(y)))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore",OptimizeWarning)
            params,_=curve_fit(_plateau_model,x,np.minimum(y,1.),p0=(1/max_time,max(0,upper_plateau*.8)),
                               bounds=([0,0],[100/max_time,max(0,upper_plateau)]),maxfev=20000)
        rate,plateau=map(float,params)
        return lambda t:_plateau_model(np.asarray(t),rate,plateau),{"rate_per_day":rate,"plateau":plateau,"parameters":2}
    raise ValueError(f"Modèle inconnu : {name}")


def select_kinetic_model(times: np.ndarray, values: np.ndarray) -> dict:
    """Select a parsimonious tail model with leave-one-time-out errors."""
    candidates=[]
    for name in ("exponential","weibull","plateau_exponential"):
        try:
            predictor,params=_fit_candidate(name,times,values)
            prediction=np.clip(predictor(times),MIN_RETENTION,2.)
            residual=np.log(np.clip(values,MIN_RETENTION,None))-np.log(prediction)
            rss=float(np.sum(np.square(residual)))
            n=len(times); k=int(params["parameters"])
            aicc=(n*math.log(max(rss/n,1e-12))+2*k+
                  (2*k*(k+1)/(n-k-1) if n>k+1 else 1e6))
            cv=[]
            if len(times)>=5:
                for index in range(1,len(times)-1):
                    mask=np.ones(len(times),dtype=bool); mask[index]=False
                    try:
                        held,_=_fit_candidate(name,times[mask],values[mask])
                        cv.append(abs(math.log(max(float(held(np.asarray([times[index]]))[0]),MIN_RETENTION))-
                                      math.log(max(float(values[index]),MIN_RETENTION))))
                    except (ValueError,RuntimeError,FloatingPointError):
                        cv.append(1.)
            cv_error=float(np.median(cv)) if cv else float(np.sqrt(np.mean(np.square(residual))))
            candidates.append({"name":name,"predictor":predictor,"parameters":params,
                               "aicc":aicc,"cv_log_error":cv_error,
                               "score":aicc+4*cv_error})
        except (ValueError,RuntimeError,FloatingPointError,OverflowError):
            continue
    if not candidates:
        predictor,params=_fit_candidate("exponential",times,values)
        candidates=[{"name":"exponential","predictor":predictor,"parameters":params,
                     "aicc":0.,"cv_log_error":0.,"score":0.}]
    chosen=min(candidates,key=lambda item:item["score"])
    return {"name":chosen["name"],"predictor":chosen["predictor"],
            "parameters":chosen["parameters"],
            "candidates":[{key:value for key,value in candidate.items() if key!="predictor"}
                          for candidate in candidates]}


def _median_profile(series: list[dict], max_time: float | None=None) -> tuple[np.ndarray,np.ndarray]:
    if max_time is None:
        max_time=min(float(item["times"][-1]) for item in series)
    points={0.,float(max_time)}
    for item in series:
        points.update(float(value) for value in item["times"] if 0<value<max_time)
    times=np.asarray(sorted(points),dtype=float)
    curves=np.asarray([np.interp(times,item["times"],item["retention"]) for item in series])
    return times,np.median(curves,axis=0)


def _experiment_holdout(series: list[dict]) -> list[dict]:
    predictions=[]
    if len(series)<3:
        return predictions
    for index,target in enumerate(series):
        training=[item for item_index,item in enumerate(series) if item_index!=index]
        max_time=min(float(item["times"][-1]) for item in training)
        train_times,train_center=_median_profile(training,max_time)
        for time,observed in zip(target["times"][1:],target["retention"][1:]):
            if float(time)>max_time:
                continue
            predicted=float(np.interp(float(time),train_times,train_center))
            predictions.append({"group":target["id"],"source_id":target["source_id"],
                                "time_days":float(time),"observed":float(observed),
                                "predicted":predicted})
    return predictions


def _temperature_holdout(series: list[dict]) -> list[dict]:
    temperatures=sorted({item["temperature_c"] for item in series if item["temperature_c"] is not None})
    predictions=[]
    if len(temperatures)<3:
        return predictions
    by_temperature={temperature:[item for item in series if item["temperature_c"]==temperature]
                    for temperature in temperatures}
    for temperature in temperatures[1:-1]:
        low=max(value for value in temperatures if value<temperature)
        high=min(value for value in temperatures if value>temperature)
        low_times,low_curve=_median_profile(by_temperature[low])
        high_times,high_curve=_median_profile(by_temperature[high])
        common_max=min(float(low_times[-1]),float(high_times[-1]))
        weight=(temperature-low)/(high-low)
        for target in by_temperature[temperature]:
            for time,observed in zip(target["times"][1:],target["retention"][1:]):
                if float(time)>common_max:
                    continue
                low_value=float(np.interp(time,low_times,low_curve))
                high_value=float(np.interp(time,high_times,high_curve))
                predicted=(1-weight)*low_value+weight*high_value
                predictions.append({"group":target["id"],"source_id":target["source_id"],
                                    "time_days":float(time),"observed":float(observed),
                                    "predicted":float(predicted)})
    return predictions


def validation_metrics(predictions: list[dict], half_width: float | None=None) -> dict:
    if not predictions:
        return {"test_predictions":0,"mae_retention":None,"rmse_retention":None,
                "mape_pct":None,"median_ape_pct":None,"max_ape_pct":None,"r2":None,
                "empirical_point_coverage_pct":None,"residuals":[]}
    observed=np.asarray([row["observed"] for row in predictions],dtype=float)
    predicted=np.asarray([row["predicted"] for row in predictions],dtype=float)
    ape=np.abs(predicted-observed)/np.maximum(np.abs(observed),MIN_RETENTION)*100
    log_residual=np.abs(np.log(np.maximum(observed,MIN_RETENTION))-
                        np.log(np.maximum(predicted,MIN_RETENTION)))
    coverage=(float(np.mean(log_residual<=half_width)*100) if half_width is not None else None)
    return {
        "test_predictions":len(predictions),
        "mae_retention":float(mean_absolute_error(observed,predicted)),
        "rmse_retention":float(math.sqrt(mean_squared_error(observed,predicted))),
        "mape_pct":float(np.mean(ape)),"median_ape_pct":float(np.median(ape)),
        "max_ape_pct":float(np.max(ape)),
        "r2":float(r2_score(observed,predicted)) if len(predictions)>=2 else None,
        "empirical_point_coverage_pct":coverage,
        "residuals":[float(value) for value in log_residual],
    }


def conformal_half_width(predictions: list[dict], coverage: float=TARGET_COVERAGE) -> float | None:
    if not predictions:
        return None
    scores=np.sort(np.asarray([
        abs(math.log(max(row["observed"],MIN_RETENTION))-
            math.log(max(row["predicted"],MIN_RETENTION))) for row in predictions
    ]))
    rank=min(len(scores)-1,max(0,int(math.ceil((len(scores)+1)*coverage))-1))
    return float(scores[rank])


def _reported_sd_half_width(series: list[dict]) -> float:
    # The predicted curve is a mean response. When n is published, use the
    # standard error of that mean; individual-specimen dispersion remains in
    # the audit and must not be confused with uncertainty on the central curve.
    relative=[float(se/max(value,MIN_RETENTION))
              for item in series for se,value in zip(item["se"],item["retention"]) if se>0]
    return float(np.quantile(relative,.90)) if relative else 0.


def _interpolation_profile(series: list[dict], temperature_c: float) -> dict:
    temperatures=sorted({item["temperature_c"] for item in series if item["temperature_c"] is not None})
    if len(temperatures)>=2 and temperatures[0]<=temperature_c<=temperatures[-1]:
        exact=[item for item in series if np.isclose(item["temperature_c"],temperature_c)]
        if exact:
            times,center=_median_profile(exact)
            return {"times":times,"center":center,"series":exact,"route":"exact_temperature_curve",
                    "temperature_range":[temperatures[0],temperatures[-1]],"exact_temperature":True}
        low=max(value for value in temperatures if value<temperature_c)
        high=min(value for value in temperatures if value>temperature_c)
        low_times,low_curve=_median_profile([item for item in series if item["temperature_c"]==low])
        high_times,high_curve=_median_profile([item for item in series if item["temperature_c"]==high])
        max_time=min(float(low_times[-1]),float(high_times[-1]))
        points=sorted({0.,max_time}|{float(value) for value in low_times if value<=max_time}|
                      {float(value) for value in high_times if value<=max_time})
        times=np.asarray(points); weight=(temperature_c-low)/(high-low)
        center=(1-weight)*np.interp(times,low_times,low_curve)+weight*np.interp(times,high_times,high_curve)
        return {"times":times,"center":center,"series":series,"route":"temperature_surface_interpolation",
                "temperature_range":[temperatures[0],temperatures[-1]],"exact_temperature":False,
                "bracketing_temperatures":[low,high]}
    times,center=_median_profile(series)
    return {"times":times,"center":center,"series":series,"route":"same_material_ensemble",
            "temperature_range":None,"exact_temperature":None}


def _crossing(days: np.ndarray, retention: np.ndarray, target: float) -> float | None:
    if target>=1: return 0.
    for index in range(1,len(days)):
        left,right=float(retention[index-1]),float(retention[index])
        if (left-target)*(right-target)<=0 and left!=right:
            fraction=(target-left)/(right-left)
            return float(days[index-1]+fraction*(days[index]-days[index-1]))
    return None


def _match_score(request: Request, series: list[dict], route: str, horizon_ratio: float) -> dict:
    score=45.; reasons=["même matériau et même propriété"]
    sources=len({item["source_id"] for item in series}); score+=min(15.,5*sources)
    if route=="exact_temperature_curve": score+=20; reasons.append("température publiée exacte")
    elif route=="temperature_surface_interpolation": score+=12; reasons.append("température encadrée par deux courbes")
    else: score+=8; reasons.append("ensemble de séries du même matériau")
    media={str(item.get("medium") or "").lower() for item in series}
    if request.exposure!="immersion" or any((request.immersion_medium or "").lower().replace("64"," 64") in value for value in media):
        score+=10; reasons.append("milieu compatible")
    if request.grade_reference:
        grade=request.grade_reference.lower()
        formulations=" ".join(str(item.get("formulation") or "").lower() for item in series)
        if any(token in formulations for token in grade.split() if len(token)>=3):
            score+=10; reasons.append("grade ou formulation retrouvé")
        else:
            score-=8; reasons.append("grade non retrouvé dans le corpus")
    if horizon_ratio>1:
        score-=min(35.,15*math.log2(max(horizon_ratio,1.)))
        reasons.append(f"horizon ×{horizon_ratio:.1f} la fenêtre observée")
    score=int(round(np.clip(score,0,100)))
    return {"score":score,"label":"Forte" if score>=80 else "Moyenne" if score>=60 else "Faible",
            "meaning":" ; ".join(reasons),"probability":False}


def predict_from_evidence(request: Request, rows: list[dict]) -> dict | None:
    """Return a SeaMat result or ``None`` when the evidence contract is not met."""
    validate_request(request)
    audit=evidence_quality(rows)
    if audit["status"]!="usable":
        return None
    usable=[row for row in audit["valid_rows"]
            if row.get("evidence_status") in {None,"source_verified_table","accepted_scientific_review"}
            and (not row.get("property_name") or "module de young" in str(row["property_name"]).lower())]
    all_series=_series(usable)
    if not all_series:
        return None
    published_temperatures=sorted({item["temperature_c"] for item in all_series
                                   if item["temperature_c"] is not None})
    if len(published_temperatures)>=2 and not published_temperatures[0]<=request.temperature_c<=published_temperatures[-1]:
        # A temperature surface must never silently become a generic material
        # ensemble outside its measured range.
        return None
    series=all_series
    if request.grade_reference:
        tokens=[token for token in request.grade_reference.lower().replace('-',' ').split() if len(token)>=3]
        grade_matches=[item for item in series
                       if tokens and any(token in str(item.get('formulation') or '').lower() for token in tokens)]
        # A routed model still needs enough independent curves for a holdout.
        # With fewer curves, retaining the full material corpus is safer and
        # the match score explicitly records that the grade is not validated.
        if len(grade_matches)>=3:
            series=grade_matches
    elif not any(item["temperature_c"] is not None for item in series):
        by_source={source_id:[item for item in series if item["source_id"]==source_id]
                   for source_id in {item["source_id"] for item in series}}
        dominant=max(by_source.values(),key=len)
        # Mixing climates and formulations can make a band wider while making
        # the central value less relevant. Prefer the densest compatible study
        # for the working curve; the other sources remain visible in the data
        # audit and can be used as external challenges as the corpus grows.
        if len(dominant)>=3:
            series=dominant
    profile=_interpolation_profile(series,request.temperature_c)
    observed_times=np.asarray(profile["times"],dtype=float)
    observed_center=np.asarray(profile["center"],dtype=float)
    max_time=float(observed_times[-1]); horizon_ratio=request.horizon_days/max_time
    kinetic=select_kinetic_model(observed_times,observed_center)
    if len(observed_times)>=3 and observed_center[-2]>observed_center[-1]>0:
        late_rate=float(math.log(observed_center[-2]/observed_center[-1])/
                        (observed_times[-1]-observed_times[-2]))
        overall_rate=max(float(-math.log(min(observed_center[-1],1.))/max_time),0.)
        if late_rate>0 and (overall_rate<=0 or late_rate<overall_rate*.85):
            kinetic["candidates"].append({"name":"tail_exponential","parameters":{"rate_per_day":late_rate,"parameters":1},
                                           "aicc":None,"cv_log_error":None,"score":"local-tail-rule"})
            kinetic={**kinetic,"name":"tail_exponential",
                     "parameters":{"rate_per_day":late_rate,"parameters":1},
                     "predictor":lambda time:_exp_model(np.asarray(time),late_rate)}
    predictor=kinetic["predictor"]
    grid=np.linspace(0,request.horizon_days,241)
    # PCHIP reproduces every observed median without oscillations caused by a
    # high-order polynomial. A selected kinetic law is used only after the
    # last observation and is anchored continuously at that point.
    interpolation=PchipInterpolator(observed_times,observed_center,extrapolate=False)
    def central_at(times: np.ndarray) -> np.ndarray:
        times=np.asarray(times,dtype=float); values=np.empty_like(times)
        inside=times<=max_time+1e-12
        values[inside]=interpolation(np.minimum(times[inside],max_time))
        if np.any(~inside):
            tail=np.asarray(predictor(times[~inside]),dtype=float)
            anchor=max(float(predictor(np.asarray([max_time]))[0]),MIN_RETENTION)
            values[~inside]=observed_center[-1]*tail/anchor
        return np.clip(values,MIN_RETENTION,2.)
    central=central_at(grid)

    holdouts=(_temperature_holdout(all_series) if profile["route"]=="temperature_surface_interpolation" else
              [] if profile["route"]=="exact_temperature_curve" else
              _experiment_holdout(series))
    half=conformal_half_width(holdouts)
    sd_half=_reported_sd_half_width(profile["series"])
    base_half=max(half or 0.,sd_half,.025)
    # Extrapolation uncertainty increases progressively; it is never hidden by
    # the narrow comparison convention from the first prototype.
    extra=np.maximum(grid/max_time-1,0)
    half_curve=base_half+.06*np.log1p(extra)
    if profile["route"]=="temperature_surface_interpolation":
        half_curve+=.03
    lower=np.clip(central*np.exp(-half_curve),0,None)
    upper=central*np.exp(half_curve)
    metrics=validation_metrics(holdouts,base_half)
    coverage=metrics.get("empirical_point_coverage_pct")
    validation_passed=bool(metrics["test_predictions"]>=6 and
                           (metrics["mape_pct"] or 1e9)<=15 and
                           (metrics["max_ape_pct"] or 1e9)<=20 and
                           (coverage is None or coverage>=75))
    source_count=len({item["source_id"] for item in series})
    if validation_passed and source_count>=2:
        evidence_level="externally_validated_short_term"
    elif validation_passed:
        evidence_level="case_calibrated_short_term"
    else:
        evidence_level="evidence_informed_short_term"
    target=request.threshold_percent/100
    crossing_horizon=max(request.horizon_days,max_time*100,36525.)
    crossing_grid=np.linspace(0,crossing_horizon,5000)
    crossing_center=central_at(crossing_grid)
    crossing_extra=np.maximum(crossing_grid/max_time-1,0)
    crossing_half=base_half+.06*np.log1p(crossing_extra)
    if profile["route"]=="temperature_surface_interpolation":
        crossing_half+=.03
    central_cross=_crossing(crossing_grid,crossing_center,target)
    fast_cross=_crossing(crossing_grid,crossing_center*np.exp(-crossing_half),target)
    slow_cross=_crossing(crossing_grid,crossing_center*np.exp(crossing_half),target)
    match=_match_score(request,series,profile["route"],horizon_ratio)
    uncertainty={
        "kind":"calibrated_log_conformal" if holdouts else "reported_sd_plus_model_floor",
        "label":f"Bande prédictive {int(TARGET_COVERAGE*100)} % calibrée" if holdouts else "Bande issue de la dispersion publiée",
        "coverage":(f"{coverage:.1f} % observés sur {metrics['test_predictions']} prédictions masquées"
                    if coverage is not None else "couverture externe non mesurable"),
        "interpretation":"Quantile conforme des erreurs logarithmiques hors échantillon, dispersion publiée et pénalité d’extrapolation.",
        "predictive_interval_validated":validation_passed and horizon_ratio<=1,"display_band":True,
        "base_half_width_pct":float((math.exp(base_half)-1)*100),
        "target_coverage_pct":TARGET_COVERAGE*100,
        "calibration":metrics,
        "source_specific":{
            "kind":"v2_holdout_validation","label":"Validation hors groupe",
            "calibration":metrics,"coverage":coverage,
        },
        "excludes":["changement de mécanisme","grade non documenté","charges mécaniques non renseignées"],
    }
    match_label=match["label"].lower()
    status=("VALIDÉ HORS ÉCHANTILLON DANS LA FENÊTRE PUBLIÉE" if validation_passed and horizon_ratio<=1 else
            "EXTRAPOLATION CALIBRÉE À CONFIRMER" if validation_passed else
            "PROFIL PUBLIÉ, VALIDATION HORS ÉCHANTILLON INSUFFISANTE")
    source_rows=[item["rows"][0] for item in series]
    source={
        "id":"+".join(sorted({item["source_id"] for item in series})),
        "title":f"Corpus SeaMat V2 · {len(series)} séries, {source_count} source(s)",
        "url":next((row.get("source_url") for row in source_rows if row.get("source_url")),None),
        "doi":next((row.get("source_doi") for row in source_rows if row.get("source_doi")),None),
        "location":f"{len(usable)} observations vérifiées ; fenêtre 0–{max_time:g} jours",
        "sources":[{"id":source_id,"title":next((row.get("source_title") for row in source_rows if row.get("source_id")==source_id),source_id),
                    "url":next((row.get("source_url") for row in source_rows if row.get("source_id")==source_id),None),
                    "doi":next((row.get("source_doi") for row in source_rows if row.get("source_id")==source_id),None),
                    "experiments":sum(item["source_id"]==source_id for item in series),
                    "extraction_methods":sorted({str(row.get("extraction_method") or "non renseignée") for row in usable if row.get("source_id")==source_id})}
                   for source_id in sorted({item["source_id"] for item in series})],
    }
    manifest={
        "model":"datasheet-screening-v6-seamat-engine",
        "engine_version":ENGINE_VERSION,"dataset":"verified-literature-routed-v2",
        "material_id":request.material_id,"material_name":request.material_name,
        "target_property":"Module de Young en traction",
        "inputs":{"e0":request.modulus_mpa,"temperature":request.temperature_c,
                  "humidity_RH":request.humidity_rh,"thickness_mm":request.thickness_mm,
                  "horizon_years":request.horizon_days/365.25,"threshold":request.threshold_percent,
                  "exposure":request.exposure,"immersion_medium":request.immersion_medium,
                  "grade_reference":request.grade_reference,"process_state":request.process_state},
        "assumptions":{"reference_half_life_years":None,"temperature_factor":1.,
                       "humidity_factor":1.,"environment_factor":1.,"thickness_factor":1.,
                       "evidence_calibrated":True,"evidence_experiments":len(series),
                       "independent_sources":source_count,"documentary_match":match,
                       "profile_method":profile["route"],"evidence_window_days":max_time,
                       "extrapolation_multiple":horizon_ratio,
                       "rate_bounds_per_day":None,"outer_crossing_interval_years":[
                           fast_cross/365.25 if fast_cross is not None else None,
                           slow_cross/365.25 if slow_cross is not None else None],
                       "selected_kinetic_model":kinetic["name"],
                       "kinetic_parameters":kinetic["parameters"],
                       "candidate_models":kinetic["candidates"],
                       "data_quality":{key:value for key,value in audit.items() if key!="valid_rows"},
                       "validation":metrics,"validation_passed":validation_passed},
        "evidence_level":evidence_level,
        "intended_use":"Estimation de recherche dans le domaine documenté et comparaison avant essais",
        "prohibited_use":"Dimensionnement de sécurité ou garantie sans qualification du grade exact",
        "validity":{"temperature_c":profile.get("temperature_range") or [request.temperature_c,request.temperature_c],
                    "humidity_rh":"conditions des publications","time_days":[0,max_time],
                    "exposure":request.exposure,"material_scope":f"{request.material_name}; correspondance {match_label}"},
        "uncertainty":uncertainty,"source":source,"status":status,
        "warnings":[
            f"La courbe est interpolée jusqu’à {max_time:g} jours ; au-delà, le modèle {kinetic['name']} prolonge la dernière observation.",
            "La bande s’appuie sur des erreurs de prédictions masquées ; elle s’élargit hors de la fenêtre publiée.",
            "Un changement de formulation, de procédé ou de mécanisme exige une nouvelle validation.",
        ],
    }
    fingerprint=sha256(json.dumps(manifest,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    result={
        "time":(grid/365.25).tolist(),"modulus":(request.modulus_mpa*central).tolist(),
        "lower":(request.modulus_mpa*lower).tolist(),"upper":(request.modulus_mpa*upper).tolist(),
        "retention":(central*100).tolist(),"crossing":(central_cross/365.25 if central_cross is not None and central_cross<=request.horizon_days else None),
        "crossing_estimate_years":central_cross/365.25 if central_cross is not None else None,
        "crossing_interval":[fast_cross/365.25 if fast_cross is not None else None,
                             slow_cross/365.25 if slow_cross is not None else None],
        "fraction_crossing":float(central_cross is not None and central_cross<=request.horizon_days),
        "rate":float(-math.log(max(central[-1],MIN_RETENTION))/max(request.horizon_days,1e-12)),
        "manifest":manifest,"fingerprint":fingerprint,"pending":False,
    }
    return result


def capability_summary(rows: list[dict]) -> dict:
    """Expose all ten V2 controls for diagnostics and the validity page."""
    audit=evidence_quality(rows)
    return {
        "engine_version":ENGINE_VERSION,
        "controls":[
            {"id":1,"name":"Contrat de données","status":"ok" if audit["status"]=="usable" else "incomplet"},
            {"id":2,"name":"Unités et valeurs finies","status":"ok" if not audit["issues"] else "à vérifier"},
            {"id":3,"name":"Bibliothèque multi-modèles","status":"actif"},
            {"id":4,"name":"Routage automatique","status":"actif"},
            {"id":5,"name":"Score de correspondance","status":"actif"},
            {"id":6,"name":"Contrôle du domaine","status":"actif"},
            {"id":7,"name":"Incertitude calibrée","status":"actif si holdouts disponibles"},
            {"id":8,"name":"Validation hors échantillon","status":"actif"},
            {"id":9,"name":"Traçabilité et empreinte","status":"actif"},
            {"id":10,"name":"Restitution et export","status":"actif"},
        ],
        "data_quality":{key:value for key,value in audit.items() if key!="valid_rows"},
    }
