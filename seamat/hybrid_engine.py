"""Learned environmental kinetics with grade/source holdouts, no invented constants.

The Arrhenius expert is activated only for compatible declining curves. Complex
non-monotonic responses remain with the measured-curve expert. Physical features
are fitted jointly; rank-deficient or unsupported transfers are rejected.
"""
from __future__ import annotations

from collections import defaultdict
import math
import numpy as np

VERSION = 'seamat-hybrid-3.0.0'
FEATURES = {
    'temperature_c': ('Température', 'ageing_temperature_c'),
    'humidity_rh': ('Humidité relative', 'humidity_rh'),
    'thickness_mm': ('Épaisseur', 'thickness_mm'),
    'crystallinity_pct': ('Cristallinité', 'crystallinity_pct'),
    'molecular_weight_g_mol': ('Masse molaire', 'molecular_weight_g_mol'),
    'reinforcement_pct': ('Taux de renfort', 'reinforcement_pct'),
}
DESCRIPTORS = {
    'density_kg_m3': ('Masse volumique (kg/m³)', 1, 30000),
    'tg_c': ('Transition vitreuse Tg (°C)', -273.14, 1000),
    'tm_c': ('Fusion Tm (°C)', -273.14, 2000),
    'crystallinity_pct': ('Cristallinité (%)', 0, 100),
    'molecular_weight_g_mol': ('Masse molaire Mn (g/mol)', 1, 1e9),
    'reinforcement_pct': ('Taux de renfort (%)', 0, 100),
    'recycled_content_pct': ('Contenu recyclé (%)', 0, 100),
}


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def validate_descriptors(material):
    for key, (label, low, high) in DESCRIPTORS.items():
        if material.get(key) not in (None, ''):
            value = number(material[key])
            if value is None or not low <= value <= high:
                raise ValueError(f'{label} : valeur attendue entre {low:g} et {high:g}.')


def _transform(key, value):
    if key == 'temperature_c':
        return 1000 * (1 / 296.15 - 1 / (value + 273.15))
    if key in ('thickness_mm', 'molecular_weight_g_mol'):
        return math.log(max(value, 1e-12))
    if key == 'humidity_rh':
        return value / 100
    return value


def _experiments(rows):
    from seamat.engine_v2 import evidence_quality
    audit = evidence_quality(rows)
    groups = defaultdict(list)
    for row in audit['valid_rows']:
        if 'module de young' not in str(row.get('property_name', '')).lower():
            continue
        if row.get('evidence_status') not in (None, 'source_verified_table', 'accepted_scientific_review'):
            continue
        groups[(str(row['source_id']), str(row['experiment_id']))].append(row)
    experiments = []
    for (source, identity), values in sorted(groups.items()):
        values.sort(key=lambda row: float(row['time_days']))
        t = np.array([float(row['time_days']) for row in values])
        e = np.array([float(row['modulus_mpa']) for row in values])
        if len(t) < 3 or t[0] != 0 or len(set(t)) != len(t):
            continue
        y = e / e[0]
        # Rigidification, induction and multiple phases cannot be silently
        # collapsed into a first-order damage law.
        rate = -float(t @ np.log(y) / (t @ t))
        fit_error = float(np.max(np.abs(np.exp(-rate * t) - y) / y) * 100)
        eligible = bool(rate > 0 and fit_error <= 10 and y[-1] < .995 and not np.any(np.diff(y) > .03))
        first = values[0]
        features = {}
        for key, (_, field) in FEATURES.items():
            observed = [number(row.get(field)) for row in values]
            admissible = all(v is not None for v in observed)
            if admissible and key == 'temperature_c': admissible = min(observed) > -273.15
            if admissible and key in ('thickness_mm', 'molecular_weight_g_mol'): admissible = min(observed) > 0
            if admissible and key in ('humidity_rh', 'crystallinity_pct', 'reinforcement_pct'): admissible = min(observed) >= 0 and max(observed) <= 100
            if admissible and np.ptp(observed) < 1e-9:
                features[key] = observed[0]
        experiments.append(dict(id=source + ':' + identity, source=source,
                                grade=str(first.get('grade_id') or first.get('formulation') or ''),
                                features=features, rate=rate, times=t, retention=y, eligible=eligible))
    return experiments


def _fit(experiments, feature_keys):
    # Keep the feature basis fixed across folds. Never choose features using
    # the hidden grade's ageing response.
    experiments = [e for e in experiments if e['eligible']]
    if not experiments:
        return None
    x = np.array([[1.] + [_transform(k, e['features'][k]) for k in feature_keys]
                  for e in experiments])
    if len(experiments) < x.shape[1] + 2 or np.linalg.matrix_rank(x) < x.shape[1]:
        return None
    coefficients = np.linalg.lstsq(x, np.log([e['rate'] for e in experiments]), rcond=None)[0]
    if 'temperature_c' in feature_keys and coefficients[1 + feature_keys.index('temperature_c')] < 0:
        return None
    return coefficients


def _rate(coefficients, features, keys):
    x = np.array([1.] + [_transform(key, features[key]) for key in keys])
    return float(np.exp(np.clip(x @ coefficients, -40, 15)))


def fit_environment_expert(rows, inputs):
    """Fit a rate law and validate it on whole unseen sources or grades.

    Returns JSON-safe diagnostics even when the expert cannot be activated.
    All unknown fields stay unknown. No training row comes from synthetic data.
    """
    experiments = _experiments(rows)
    audit = {'active': False, 'expert': 'arrhenius_environment',
             'eligible_experiments': sum(e['eligible'] for e in experiments), 'reason': '', 'features': []}
    if audit['eligible_experiments'] < 6:
        audit['reason'] = 'Au moins six séries compatibles avec une cinétique décroissante sont requises.'
        return audit
    keys = [key for key in FEATURES if all(key in e['features'] for e in experiments)
            and len({e['features'][key] for e in experiments}) >= 3
            and not (key == 'humidity_rh' and inputs.get('exposure') == 'immersion')]
    if not keys:
        audit['reason'] = 'Aucun effet environnemental identifiable dans ces séries.'
        return audit
    audit['features'] = keys
    domains = {key: [min(e['features'][key] for e in experiments),
                     max(e['features'][key] for e in experiments)] for key in keys}
    audit['domains'] = domains
    query = {k: number(inputs.get(k)) for k in keys}
    if any(query[k] is None or not domains[k][0] <= query[k] <= domains[k][1] for k in keys):
        audit['reason'] = 'Paramètre manquant ou hors du domaine appris.'
        return audit
    # Being inside each marginal range is insufficient: the combination itself
    # must be represented by the joint experimental domain.
    from scipy.optimize import linprog
    coordinates=np.array([[_transform(k,e['features'][k]) for k in keys] for e in experiments])
    point=np.array([_transform(k,query[k]) for k in keys])
    scales=np.maximum(np.ptp(coordinates,axis=0),1e-12)
    hull=linprog(np.zeros(len(experiments)),
                 A_eq=np.vstack([np.ones(len(experiments)), (coordinates/scales).T]),
                 b_eq=np.r_[1.,point/scales],bounds=(0,None),method='highs')
    if not hull.success:
        audit['reason']='La combinaison de paramètres sort du domaine expérimental conjoint.'
        return audit
    sources = {e['source'] for e in experiments}
    grades = {e['grade'] for e in experiments}
    grouping = 'source' if len(sources) >= 3 else 'grade' if len(grades) >= 3 and '' not in grades else None
    if not grouping:
        audit['reason'] = 'Trois sources ou trois grades identifiés sont nécessaires au test de transfert.'
        return audit
    predictions = []
    for group in sorted({e[grouping] for e in experiments}):
        train = [e for e in experiments if e[grouping] != group]
        model = _fit(train, keys)
        if model is None:
            audit['reason'] = 'Effets confondus ou entraînement insuffisant après masquage du groupe.'
            return audit
        for experiment in (e for e in experiments if e[grouping] == group):
            rate = _rate(model, experiment['features'], keys)
            for t, y in zip(experiment['times'][1:], experiment['retention'][1:]):
                predicted = float(np.exp(-rate * t))
                predictions.append({'group': group, 'source_id': experiment['source'],
                                    'time_days': float(t), 'observed': float(y), 'predicted': predicted})
    from seamat.engine_v2 import validation_metrics
    validation = validation_metrics(predictions)
    audit.update(validation=validation, validation_protocol='leave_one_' + grouping + '_out',
                 predictions=predictions)
    if validation['mape_pct'] > 10 or validation['max_ape_pct'] > 20:
        audit['reason'] = 'Le test de transfert dépasse 10 % d’erreur moyenne ou 20 % au maximum.'
        return audit
    model = _fit(experiments, keys)
    if model is None:
        audit['reason'] = 'La loi thermique ou les effets identifiés ne sont pas admissibles.'
        return audit
    audit.update(active=True, reason='Cinétique apprise, contrôle interne par groupes réussi.',
                 rate_per_day=_rate(model, query, keys),
                 coefficients=[float(c) for c in model],
                 time_window_days=min(float(e['times'][-1]) for e in experiments))
    if 'temperature_c' in keys:
        audit['activation_energy_kj_mol'] = float(model[1 + keys.index('temperature_c')] * 8.314462618)
    return audit


def apply_environment_expert(result, audit):
    """Update every curve/threshold consistently when the learned law is usable."""
    manifest = result['manifest']
    manifest['hybrid_engine'] = {'version': VERSION, **audit}
    if not audit['active']:
        return result
    days = np.asarray(result['time']) * 365.25
    initial = float(manifest['inputs']['e0'])
    rate = audit['rate_per_day']
    retention = np.exp(-rate * days)
    from seamat.engine_v2 import conformal_half_width, validation_metrics
    half = max(float(conformal_half_width(audit['predictions']) or 0), .001)
    # Uncertainty starts at zero conditional on a known E0. It grows to the
    # empirical residual band within the observed time scale.
    ramp = np.minimum(days / audit['time_window_days'], 1)
    widths = half * ramp + .06 * np.log1p(np.maximum(days / audit['time_window_days'] - 1, 0))
    result.update(modulus=(initial * retention).tolist(), retention=(100 * retention).tolist(),
                  lower=(initial * retention * np.exp(-widths)).tolist(),
                  upper=(initial * retention * np.exp(widths)).tolist(), rate=rate)
    for stale in ('outer_lower', 'outer_upper'):
        result.pop(stale, None)
    target = manifest['inputs']['threshold'] / 100
    crossing = -math.log(target) / rate / 365.25
    result.update(crossing_estimate_years=crossing,
                  crossing=crossing if crossing <= days[-1] / 365.25 else None,
                  crossing_interval=[None, None], fraction_crossing=float(crossing <= days[-1] / 365.25))
    assumptions = manifest['assumptions']
    assumptions.update(profile_method='learned_environment_kinetics', selected_kinetic_model='arrhenius_environment',
                       evidence_window_days=audit['time_window_days'],
                       extrapolation_multiple=float(days[-1] / audit['time_window_days']),
                       validation=validation_metrics(audit['predictions'], half),
                       kinetic_parameters={'rate_per_day': rate, 'coefficients': audit['coefficients']})
    assumptions['validation_passed']=True
    manifest['engine_version'] = VERSION
    manifest['uncertainty'].update(kind='empirical_environment_residuals',
                                  label='Bande empirique du transfert environnemental',
                                  calibration=assumptions['validation'],
                                  source_specific={'kind':'v2_holdout_validation','calibration':assumptions['validation']},
                                  interpretation='Erreurs de transfert par groupes masqués ; couverture externe non établie.',
                                  predictive_interval_validated=False,
                                  base_half_width_pct=float(np.expm1(half) * 100))
    return result
