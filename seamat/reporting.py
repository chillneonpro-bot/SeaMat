"""Human-readable, reproducible reports for simulations and observations."""
from __future__ import annotations

from datetime import datetime, timezone

from seamat.modeling import (curve_value_origin, evidence_assessment,
                              format_years_months, sampled_curve_rows)


def _clean(value: object) -> str:
    return str(value if value is not None else 'Non renseigné').replace('\n',' ').strip()


def markdown_report(result: dict, title: str = 'Rapport SeaMat') -> bytes:
    manifest=result.get('manifest',{}); inputs=manifest.get('inputs',{}); model=str(manifest.get('model','inconnu'))
    title=_clean(title)[:200]; status=_clean(manifest.get('status','Statut inconnu'))
    display=inputs.get('horizon_display',{}) if model.startswith(('datasheet-screening-', 'datasheet-analog-')) else {}
    unit={'days':'jours','months':'mois','years':'années'}.get(display.get('unit'),'années' if model.startswith(('datasheet-screening-', 'datasheet-analog-')) else 'jours')
    reliability=manifest.get('reliability') or {}
    lines=[f'# {title}','',f'**Généré le :** {datetime.now(timezone.utc).isoformat()}',
           f'**Modèle :** `{model}`',
           f'**Moteur :** `{_clean(manifest.get("engine_version", "Non renseigné"))}`',
           f'**Statut :** {status}',
           f'**Qualification :** {_clean(reliability.get("label","Non évaluée"))}',
           f'**Décision :** {_clean(reliability.get("decision","Non évaluée"))}',
           f'**Empreinte :** `{_clean(result.get("fingerprint"))}`','']
    if model.startswith(('datasheet-screening-', 'datasheet-analog-')):
        assessment=evidence_assessment(result)
        crossing=result.get('crossing_estimate_years'); lo,hi=result.get('crossing_interval',[None,None])
        horizon_text=display.get('label') or f"{float(inputs['horizon_years']):g} ans"
        lines += ['## Résultat', '', f"- Matériau : {_clean(manifest.get('material_name'))}",
                  f"- Grade / référence : {_clean(inputs.get('grade_reference'))}",
                  f"- Procédé / état : {_clean(inputs.get('process_state'))}",
                  f"- Niveau de preuve : {assessment['level']} — {assessment['label']}",
                  f"- Module initial : {float(inputs['e0']):g} MPa",
                  f"- Module conservé à l’horizon : {float(result['retention'][-1]):.1f} %",
                  f"- Origine de la valeur à l’horizon : {curve_value_origin(result)}",
                  f"- Franchissement central : {format_years_months(float(crossing)) if crossing is not None else 'Non atteint'}",
                  f"- Plage prédictive du franchissement : {format_years_months(float(lo)) if lo is not None else 'Non déterminée'} à {format_years_months(float(hi)) if hi is not None else 'Non déterminée'}",
                  '', '## Paramètres', '',
                  f"- Température : {float(inputs['temperature']):g} °C",
                  f"- Humidité relative : {float(inputs['humidity_RH']):g} %",
                  f"- Épaisseur : {float(inputs['thickness_mm']):g} mm",
                  f"- Milieu : {_clean(inputs['exposure'])}",
                  f"- Horizon saisi : {_clean(horizon_text)}",
                  f"- Seuil : {float(inputs['threshold']):g} %",'']
    elif model.startswith('piecewise-linear-published-'):
        lines += ['## Résultat', '', f"- Série : {_clean(manifest.get('experiment_id'))}",
                  f"- Module initial : {float(inputs['e0']):g} MPa",
                  f"- Module conservé à l’horizon : {float(result['retention'][-1]):.1f} %",
                  f"- Origine de la valeur à l’horizon : {curve_value_origin(result)}",
                  f"- Horizon : {float(inputs['horizon_days']):g} jours",
                  '- Méthode : interpolation linéaire entre les temps publiés, sans extrapolation','']
    else:
        crossing=result.get('crossing')
        lines += ['## Résultat pédagogique', '',
                  f"- Module initial : {float(inputs.get('e0',result['modulus'][0])):g} MPa",
                  f"- Module conservé à l’horizon : {float(result['retention'][-1]):.1f} %",
                  f"- Origine de la valeur à l’horizon : {curve_value_origin(result)}",
                  f"- Franchissement : {float(crossing):g} jours" if crossing is not None else '- Franchissement : non atteint',
                  '- Nature : scénario synthétique, sans validation matérielle','']
    precision=manifest.get('precision') or {}
    if precision:
        measured=precision.get('reference_precision_pct')
        value=(f"{measured:.1f} % à ±{precision['tolerance_pct']:g} %" if measured is not None else 'Non mesurée')
        lines += ['## Précision mesurée','',f'- Sur les références : {value}',
                  f"- Comparaisons masquées : {precision['success_count']}/{precision['prediction_count']} ; {precision['group_count']} groupes",
                  f"- Votre grade : {precision['target_status']}",
                  f"- Portée : {precision['scope']}",
                  f"- Description renseignée : {precision['completeness_pct']} % (ce n’est pas une précision)",'']
        lines += [f"- {_clean(check['parameter'])} : {_clean(check['status'])}. {_clean(check['detail'])}" for check in precision['domain_checks']]
        lines += ['']
    physics=manifest.get('family_physics') or {}
    if physics:
        from seamat.family_physics import PARAMETERS,MECHANISMS
        lines += ['## Modèle par mécanismes','',f"- Famille : {physics['family']['label']}",
                  '- Mécanismes : '+', '.join(MECHANISMS[k] for k in physics['mechanisms']),
                  '- Référence des coefficients : '+_clean(physics['source']),
                  '- Formule : '+physics['formula'],'']
        lines += [f"- {PARAMETERS[key][0]} : {value:g} ; bornes {_clean(physics['bounds'].get(key))}" for key,value in physics['parameters'].items()]
        lines += ['']
    warnings=manifest.get('warnings',[])
    if warnings:
        lines += ['## Limites','']+[f'- {_clean(item)}' for item in warnings]+['']
    if manifest.get('prohibited_use'):
        lines += [f"**Usage interdit :** {_clean(manifest['prohibited_use'])}",'']
    source=manifest.get('source') or {}
    if source:
        lines += ['## Source','',f"- {_clean(source.get('title') or source.get('id'))}",
                  f"- {_clean(source.get('url') or source.get('location'))}",'']
    rows=sampled_curve_rows(result,time_unit=None if model.startswith(('datasheet-screening-', 'datasheet-analog-')) else unit)
    lines += ['## Valeurs principales','',f'| Temps ({unit}) | Module central (MPa) | Borne basse | Borne haute | Conservation (%) | Origine |',
              '|---:|---:|---:|---:|---:|:---|']
    lines += [f"| {row['temps']:g} | {row['module_mpa']:g} | {row['module_min_mpa']:g} | {row['module_max_mpa']:g} | {row['retention_pct']:g} | {row['origine']} |" for row in rows]
    lines += ['', '---', 'Ce rapport décrit le calcul et les données disponibles dans SeaMat. Il ne constitue pas une qualification industrielle.','']
    return '\n'.join(lines).encode('utf-8')
