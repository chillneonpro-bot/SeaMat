"""Input-dependent precision report. Completeness is never a probability.

Accuracy = observed fraction within an explicit relative-error tolerance.
Reference CV, target applicability and frozen external validation stay distinct.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
import numpy as np

from seamat.hybrid_engine import (DESCRIPTORS, VERSION, number, validate_descriptors,
                                 fit_environment_expert, apply_environment_expert)


STANDARD_RATE_MULTIPLIERS = (.95, 1.05)


def apply_standardized_comparison_band(result):
    """Apply the same visible ±5 % ageing-speed convention to projections.

    The evidence-derived interval is retained verbatim under ``source_specific``.
    Published measurement curves and user-supplied coefficient bounds keep their
    own bands because they are not generic datasheet projections.
    """
    manifest=result.get('manifest') or {}
    if manifest.get('model','').startswith('piecewise-linear-published-'):
        return result
    if (manifest.get('family_physics') or {}).get('active'):
        return result
    uncertainty=manifest.get('uncertainty') or {}
    if uncertainty.get('kind')=='standardized_rate_sensitivity':
        return result
    inputs=manifest.get('inputs') or {}
    e0=number(inputs.get('e0'))
    central=np.asarray(result.get('modulus') or [],dtype=float)
    if e0 is None or e0<=0 or not len(central) or np.any(central<=0):
        return result
    slow,fast=STANDARD_RATE_MULTIPLIERS
    damage=-np.log(np.clip(central/e0,1e-12,None))
    scenarios=np.vstack((e0*np.exp(-slow*damage),e0*np.exp(-fast*damage)))
    result['lower']=np.min(scenarios,axis=0).tolist()
    result['upper']=np.max(scenarios,axis=0).tolist()
    crossing=number(result.get('crossing_estimate_years'))
    result['crossing_interval']=([crossing/fast,crossing/slow] if crossing is not None else [None,None])
    assumptions=manifest.setdefault('assumptions',{})
    rate=number(result.get('rate'))
    assumptions['rate_bounds_per_day']=([rate*slow,rate*fast] if rate is not None else None)
    manifest['uncertainty']={
        'kind':'standardized_rate_sensitivity',
        'label':'Plage standardisée · 10 % au total',
        'coverage':'même convention de comparaison pour toutes les projections',
        'interpretation':('La borne rapide applique ×1,05 à la vitesse de vieillissement et la borne lente '
                          '×0,95. La bande scientifique d’origine reste disponible dans source_specific.'),
        'predictive_interval_validated':False,'display_band':True,
        'rate_multipliers':[slow,fast],
        'calibration':uncertainty.get('calibration'),
        'source_specific':uncertainty,
        'excludes':['garantie statistique universelle','transfert vers un autre grade','variabilité entre lots'],
    }
    return result


def precision_report(result, material, rows, tolerance_pct=5.):
    tolerance = number(tolerance_pct)
    if tolerance is None or not 0 < tolerance <= 50:
        raise ValueError('La tolérance de précision doit être comprise entre 0 et 50 %.')
    manifest = result['manifest']; inputs = manifest['inputs']; assumptions = manifest.get('assumptions', {})
    hybrid = manifest.get('hybrid_engine') or {}
    trained_features = set(hybrid.get('features') or []) if hybrid.get('active') else set()
    if assumptions.get('profile_method') in ('exact_temperature_curve', 'temperature_surface_interpolation'):
        trained_features.add('temperature_c')
    source_ids = {s['id'] for s in (manifest.get('source', {}).get('sources') or [])}
    from seamat.engine_v2 import evidence_quality
    reference = [r for r in evidence_quality(rows)['valid_rows'] if r.get('source_id') in source_ids]
    horizon = float(inputs.get('horizon_years') or 0) * 365.25
    validation = assumptions.get('validation') or {}
    predictions = [p for p in validation.get('predictions', []) if 0 < p['time_days'] <= horizon + 1e-9]
    errors = [abs(p['predicted'] - p['observed']) / abs(p['observed']) * 100 for p in predictions]
    groups = defaultdict(list)
    for p, error in zip(predictions, errors):
        groups[p['group']].append(error <= tolerance)
    checks = []
    for label, field, requested in (
        ('Température', 'ageing_temperature_c', inputs.get('temperature')),
        ('Humidité relative', 'humidity_rh', inputs.get('humidity_RH')),
        ('Épaisseur', 'thickness_mm', inputs.get('thickness_mm')),
    ):
        if field == 'humidity_rh' and inputs.get('exposure') == 'immersion':
            checks.append({'parameter': label, 'status': 'Sans objet', 'detail': 'Humidité de l’air ignorée en immersion.', 'compatible': True})
            continue
        known = [number(r.get(field)) for r in reference]
        known = [v for v in known if v is not None]
        if not known:
            status, detail, compatible = 'Non caractérisé', 'Effet non appris ; conditions publiées incomplètes.', False
        elif number(requested) is not None and min(known) - 1e-9 <= float(requested) <= max(known) + 1e-9:
            status, detail, compatible = 'Dans le domaine', f'Conditions publiées : {min(known):g} à {max(known):g}.', True
        else:
            status, detail, compatible = 'Hors domaine', f'Valeur saisie {requested} ; références {min(known):g} à {max(known):g}.', False
        learned_key='temperature_c' if field=='ageing_temperature_c' else field
        if compatible and max(known)-min(known)>1e-9 and learned_key not in trained_features:
            status, detail, compatible='Effet non appris', 'La plage est documentée mais son effet n’est pas identifié par la loi retenue.', False
        checks.append({'parameter': label, 'status': status, 'detail': detail, 'compatible': compatible})
    window = number(assumptions.get('evidence_window_days'))
    checks.append({'parameter': 'Durée', 'status': 'Dans le domaine' if window and horizon <= window else 'Hors domaine',
                   'detail': f'Fenêtre publiée : {window:g} jours.' if window else 'Aucune série temporelle compatible.',
                   'compatible': bool(window and horizon <= window)})
    grade = str(inputs.get('grade_reference') or '').strip().casefold()
    grades = {str(r.get('grade_id') or r.get('formulation') or '').strip().casefold() for r in reference}
    exact_grade = bool(grade and grade in grades and not assumptions.get('analog_transfer'))
    checks.append({'parameter': 'Grade / formulation', 'status': 'Identifié' if exact_grade else 'Transfert non validé',
                   'detail': 'Référence exacte retrouvée.' if exact_grade else 'La précision des références ne garantit pas celle de votre grade.',
                   'compatible': exact_grade})
    descriptors = []
    for key, (label, _, _) in DESCRIPTORS.items():
        value = number(material.get(key))
        descriptors.append({'parameter': label, 'value': value, 'status':
                            'Contrôle du domaine thermique' if value is not None and key in ('tg_c','tm_c') and manifest.get('family_physics') else
                            'Utilisé par la loi apprise' if key in trained_features else
                            'Renseigné · effet non appris' if value is not None else 'À renseigner'})
    identity = {'grade': inputs.get('grade_reference'), 'process': inputs.get('process_state'),
                'base': material.get('base_polymer') or (material.get('id') if not material.get('custom') else None),
                'stabilizers': material.get('stabilizers')}
    known_identity = sum(bool(str(v or '').strip()) and str(v).lower() not in ('inconnu', 'non renseigné', 'non connu') for v in identity.values())
    supplied = sum(row['value'] is not None for row in descriptors) + known_identity
    completeness = round(100 * supplied / (len(descriptors) + len(identity)))
    success = sum(error <= tolerance for error in errors)
    percent = success / len(errors) * 100 if errors else None
    for key,(label,_,_) in DESCRIPTORS.items():
        value=number(material.get(key))
        if value is None: continue
        known=[number(r.get(key)) for r in reference]
        known=[v for v in known if v is not None]
        valid=bool(known and min(known)-1e-9<=value<=max(known)+1e-9
                   and (max(known)-min(known)<1e-9 or key in trained_features))
        checks.append({'parameter':label,'status':'Dans le domaine' if valid else 'Effet non validé',
                       'detail':'Valeur représentée dans le corpus.' if valid else 'Aucun transfert validé pour cette propriété.',
                       'compatible':valid})
    compatible = all(c['compatible'] for c in checks)
    target = percent if compatible and len(groups) >= 3 and not material.get('custom') else None
    return {
        'version': VERSION, 'tolerance_pct': tolerance,
        'definition': f'Part des prédictions masquées dont l’erreur relative est inférieure ou égale à {tolerance:g} %.',
        'reference_precision_pct': percent, 'target_precision_pct': target,
        'prediction_count': len(errors), 'success_count': success, 'group_count': len(groups),
        'successful_groups': sum(all(values) for values in groups.values()),
        'mean_relative_error_pct': float(np.mean(errors)) if errors else None,
        'maximum_relative_error_pct': max(errors) if errors else None,
        'scope': 'Validation croisée interne ; aucune garantie individuelle ni qualification externe.',
        'target_status': 'Référence interne applicable' if target is not None else 'Précision du grade non établie',
        'external_precision_pct': None, 'external_qualified': False,
        'scored_quantity': 'Rétention du module E/E₀, pas durée de vie ni temps au seuil.',
        'threshold_precision_pct': None,
        'completeness_pct': completeness, 'completeness_meaning': 'Complétude de la description, pas probabilité de justesse.',
        'domain_checks': checks, 'descriptors': descriptors,
        'priorities': [c['parameter'] + ' : ' + c['detail'] for c in checks if not c['compatible']],
        'mechanisms': str(material.get('mechanisms') or 'Non renseignés'),
        'predictions': [{'group': p['group'], 'time_days': p['time_days'],
                         'observed_retention': p['observed'], 'predicted_retention': p['predicted'],
                         'relative_error_pct': error, 'within_tolerance': error <= tolerance}
                        for p, error in zip(predictions, errors)],
    }


def finalize_prediction(result, material, evidence_rows, tolerance_pct=5.):
    validate_descriptors(material)
    rows = evidence_rows
    assumptions = result['manifest'].get('assumptions') or {}
    analog = assumptions.get('analog_transfer')
    if analog:
        from seamat import material_db
        rows = material_db.model_evidence_rows(analog['source_material_id'], result['manifest']['inputs']['exposure'])
    inputs = result['manifest']['inputs']
    query = {**material, 'temperature_c': inputs.get('temperature'),
             'humidity_rh': inputs.get('humidity_RH'), 'thickness_mm': inputs.get('thickness_mm'),
             'exposure': inputs.get('exposure')}
    # Kinetics may only be learned from the already routed, compatible corpus.
    ids = {s['id'] for s in result['manifest'].get('source', {}).get('sources', [])}
    compatible = [r for r in rows if r.get('source_id') in ids] if ids else []
    from seamat.family_physics import apply_family_physics
    physical=bool((material.get('physics_model') or {}).get('enabled'))
    expert = (dict(active=False,features=[],reason='Les coefficients du modèle par mécanismes sont fournis explicitement.')
              if physical else fit_environment_expert(compatible, query))
    if analog and not physical:
        # Source validation is not target-grade validation. Retain the existing
        # analogue band until its transfer has its own held-out benchmark.
        expert.update(active=False, reason='Transfert vers un nouveau grade : validation des paramètres requise.')
    result = apply_environment_expert(result, expert)
    result = apply_family_physics(result,material)
    result = apply_standardized_comparison_band(result)
    result['manifest']['material_description'] = {k: material.get(k) for k in
        [*DESCRIPTORS, 'base_polymer', 'stabilizers', 'reinforcement', 'process_state', 'grade_reference']}
    result['manifest']['material_description']['physics_model']=material.get('physics_model')
    for key in ('grade_reference','process_state'):
        result['manifest']['material_description'][key]=inputs.get(key)
    from seamat.reliability import apply_reliability_gate
    result = apply_reliability_gate(result)
    report = precision_report(result, material, rows, tolerance_pct)
    result['manifest']['precision'] = report
    result['manifest']['inputs']['precision_tolerance_pct'] = float(tolerance_pct)
    result['fingerprint'] = sha256(json.dumps(result['manifest'], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return result
