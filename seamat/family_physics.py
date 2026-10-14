"""Explicit, parameterised polymer mechanisms for prospective research.

No coefficients are inferred from E0 or from a family name. Parameters and their
source are provided by the caller; family templates describe candidate mechanisms,
not their prevalence or validation. This is a reduced-order model, not a full
reaction-diffusion solver. All time-dependent coefficients use days, D uses m²/s.
"""
from __future__ import annotations

import itertools
import math
import unicodedata
import numpy as np
from scipy.optimize import brentq

from seamat.hybrid_engine import number

VERSION='seamat-family-physics-1.0.0'
MECHANISMS={'thermal':'Dégradation thermique', 'uv':'Photo-vieillissement',
            'hydrolysis':'Hydrolyse', 'plasticization':'Plastification par l’eau',
            'stiffening':'Rigidification / post-réticulation'}
# label, lower, upper, group; None is always missing, zero is deliberate.
PARAMETERS={
    'reference_temperature_c':('Température de référence des coefficients (°C)',-40,160,'common'),
    'residual_fraction':('Fraction de rigidité résistante à la dégradation (0–1)',0,1,'common'),
    'thermal_rate_day':('Vitesse thermique à la référence (jour⁻¹)',0,100,'thermal'),
    'thermal_ea_kj_mol':('Énergie d’activation thermique (kJ/mol)',0,400,'thermal'),
    'uv_rate_day':('Vitesse UV à l’irradiance de référence (jour⁻¹)',0,100,'uv'),
    'uv_ea_kj_mol':('Énergie d’activation UV (kJ/mol)',0,400,'uv'),
    'uv_reference_w_m2':('Irradiance UV de référence (W/m²)',1e-9,10000,'uv'),
    'uv_irradiance_w_m2':('Irradiance UV appliquée, même bande spectrale (W/m²)',0,10000,'uv'),
    'uv_exponent':('Exposant de réponse à l’irradiance',.01,5,'uv'),
    'diffusion_m2_s':('Diffusivité de l’eau à la référence (m²/s)',1e-20,1e-5,'water'),
    'diffusion_ea_kj_mol':('Énergie d’activation de diffusion (kJ/mol)',0,400,'water'),
    'sorption_exponent':('Exposant de sorption en air humide',.01,10,'water'),
    'hydrolysis_rate_day':('Vitesse d’hydrolyse à saturation (jour⁻¹)',0,100,'hydrolysis'),
    'hydrolysis_ea_kj_mol':('Énergie d’activation d’hydrolyse (kJ/mol)',0,400,'hydrolysis'),
    'plasticization_fraction':('Perte relative réversible à saturation (0–1)',0,.999,'plasticization'),
    'stiffening_rate_day':('Vitesse de rigidification (jour⁻¹)',0,100,'stiffening'),
    'stiffening_ea_kj_mol':('Énergie d’activation de rigidification (kJ/mol)',0,400,'stiffening'),
    'stiffening_gain':('Gain relatif maximal de rigidification',0,10,'stiffening'),
}
COMMON_FAMILIES={
 'polyolefine':'thermoplastic', 'polyolefine cyclique':'thermoplastic',
 'polymere styrenique':'thermoplastic', 'polymere acrylique':'thermoplastic',
 'polymere halogene':'thermoplastic', 'polymere vinylique':'thermoplastic',
 'copolymere':'thermoplastic', 'polymere technique':'thermoplastic',
 'polyamide':'hydrophilic', 'polyamide haute performance':'hydrophilic',
 'polyester':'hydrophilic', 'polyester biodegradable':'hydrophilic',
 'polymere biodegradable':'hydrophilic', 'polyurethane':'hydrophilic',
 'thermodurcissable':'network', 'composite biosource':'composite',
 'elastomere':'elastomer', 'elastomere fluore':'elastomer',
 'elastomere thermoplastique':'elastomer', 'polyamide elastomere':'elastomer',
 'polyester elastomere':'elastomer', 'fluoropolymere':'resistant',
 'polyimide':'resistant', 'polymere haute performance':'resistant',
}
TEMPLATES={
 'thermoplastic':('Thermoplastiques', ['thermal','uv','stiffening']),
 'hydrophilic':('Polymères sensibles à l’eau', ['thermal','hydrolysis','plasticization']),
 'network':('Réseaux thermodurcissables', ['thermal','plasticization','hydrolysis','stiffening']),
 'elastomer':('Élastomères et réseaux souples', ['thermal','uv','plasticization','stiffening']),
 'composite':('Composites — propriétés effectives mesurées', ['thermal','hydrolysis','plasticization']),
 'resistant':('Polymères techniques à haute stabilité', ['thermal','uv']),
}
REFERENCES=[
 {'title':'NIST — Kinetics Based Models to Describe Environmental Degradation of Polymeric Sealants',
  'url':'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=922362',
  'scope':'Forme de relaxation vers un plateau ; module de relaxation des mastics, pas calibration universelle du module de Young.'},
 {'title':'Influence of Thickness on Water Absorption and Tensile Strength of BFRP Laminates',
  'url':'https://doi.org/10.3390/app10103618',
  'scope':'Solution de diffusion de Fick dans une plaque ; aucune valeur de résistance convertie en module.'},
 {'title':'NIST — Temperature and light intensity effects on the photodegradation of HDPE',
  'url':'https://www.nist.gov/publications/temperature-and-light-intensity-effects-photodegradation-high-density-polyethylene',
  'scope':'Une hausse de rigidité peut accompagner le vieillissement ; ne pas imposer une diminution universelle.'},
]


def family_plan(material):
    raw=unicodedata.normalize('NFKD',str(material.get('family') or '')).casefold()
    name=' '.join(''.join(c for c in raw if not unicodedata.combining(c)).split())
    key=COMMON_FAMILIES.get(name)
    if not key and material.get('base_polymer'):
        from seamat import material_db
        base=material_db.material(str(material['base_polymer']).strip().upper())
        if base: return {**family_plan(base),'resolved_from_base':base['id']}
    label,candidates=TEMPLATES.get(key,('Famille à identifier',[]))
    return {'version':VERSION,'family_code':key or 'unknown','label':label,
            'candidate_mechanisms':candidates,'supported':key is not None,
            'meaning':'Mécanismes candidats ; leur activation exige des coefficients propres au grade et au milieu.'}


def validate_config(config):
    if not isinstance(config,dict): raise ValueError('La configuration cinétique doit être un objet.')
    selected=config.get('mechanisms') or []
    if not isinstance(selected,list) or not selected or any(k not in MECHANISMS for k in selected):
        raise ValueError('Choisissez au moins un mécanisme cinétique reconnu.')
    params=config.get('parameters') or {}
    if not isinstance(params,dict): raise ValueError('Les coefficients doivent être nommés.')
    for key,value in params.items():
        if key not in PARAMETERS: raise ValueError('Coefficient inconnu : '+str(key))
        if value in (None,''): continue
        label,low,high,_=PARAMETERS[key]
        if number(value) is None or not low<=float(value)<=high:
            raise ValueError(f'{label} : valeur finie attendue entre {low:g} et {high:g}.')
    bounds=config.get('bounds') or {}
    if not isinstance(bounds,dict) or len(bounds)>8:
        raise ValueError('Définissez au maximum huit coefficients avec bornes simultanées.')
    for key,bound in bounds.items():
        if key not in params or number(params[key]) is None or key not in PARAMETERS:
            raise ValueError('Une borne exige un coefficient central connu : '+str(key))
        if not isinstance(bound,(list,tuple)) or len(bound)!=2 or any(number(v) is None for v in bound):
            raise ValueError('Chaque borne doit contenir deux nombres finis : '+key)
        lo,hi=map(float,bound); _,minimum,maximum,_=PARAMETERS[key]
        if not minimum<=lo<=float(params[key])<=hi<=maximum:
            raise ValueError('Bornes incohérentes avec le coefficient central : '+key)
    if not str(config.get('source') or '').strip():
        raise ValueError('Indiquez la référence des coefficients ou « hypothèse de recherche ».')


def _required(p,key):
    value=number(p.get(key))
    if value is None: raise ValueError('Coefficient requis : '+PARAMETERS[key][0])
    return value


def _arrhenius(p,prefix,temperature):
    rate=_required(p,prefix+'_rate_day')
    reference=_required(p,'reference_temperature_c')
    # Even k=0 at one temperature does not identify Ea, but its zero scenario
    # is invariant. Otherwise transfer in T requires a measured/provided Ea.
    if rate==0 or abs(temperature-reference)<1e-9: return rate
    ea=_required(p,prefix+'_ea_kj_mol')
    lograte=math.log(rate)+ea*1000/8.314462618*(1/(reference+273.15)-1/(temperature+273.15))
    if lograte>50: raise ValueError('Vitesse hors résolution : réduire la température ou vérifier les coefficients.')
    return math.exp(lograte)


def slab_uptake(days,diffusivity,thickness_mm):
    """Mean uptake and its exact time integral, initially dry two-face slab.

    Small Fourier times use the semi-infinite asymptote to avoid subtractive
    cancellation. At Fo=.01 the neglected opposite-face term is negligible.
    """
    t=np.asarray(days,dtype=float); alpha=diffusivity*86400/(thickness_mm/1000)**2
    fo=alpha*t
    uptake=np.zeros_like(t); integral=np.zeros_like(t)
    small=(fo>0)&(fo<.01)
    uptake[small]=4*np.sqrt(fo[small]/np.pi)
    integral[small]=8/3*math.sqrt(alpha/np.pi)*t[small]**1.5
    large=fo>=.01
    odd=2*np.arange(100)+1
    lam=np.pi**2*alpha*odd**2
    if np.any(large):
        exp=np.exp(-t[large,None]*lam)
        uptake[large]=1-8/np.pi**2*np.sum(exp/odd**2,axis=1)
        integral[large]=t[large]-8/np.pi**2*np.sum(-np.expm1(-t[large,None]*lam)/(odd**2*lam),axis=1)
    return np.clip(uptake,0,1),np.maximum(integral,0)


def _response(days,inputs,p,selected):
    t=np.asarray(days,dtype=float); temperature=float(inputs['temperature'])
    damage=np.zeros_like(t); water=np.zeros_like(t); gain=np.ones_like(t)
    effects={}
    if 'thermal' in selected:
        rate=_arrhenius(p,'thermal',temperature); damage+=rate*t
        effects['thermal_rate_at_conditions_day']=rate
    if 'uv' in selected:
        rate=_arrhenius(p,'uv',temperature)
        irradiation=_required(p,'uv_irradiance_w_m2'); reference=_required(p,'uv_reference_w_m2')
        exponent=_required(p,'uv_exponent')
        rate*= (irradiation/reference)**exponent
        damage+=rate*t; effects['uv_rate_at_conditions_day']=rate
    if {'hydrolysis','plasticization'} & set(selected):
        d=_required(p,'diffusion_m2_s'); reference=_required(p,'reference_temperature_c')
        if abs(temperature-reference)>1e-9:
            ea=_required(p,'diffusion_ea_kj_mol')
            factor=ea*1000/8.314462618*(1/(reference+273.15)-1/(temperature+273.15))
            if factor>50: raise ValueError('Diffusion hors résolution : vérifier la température et les coefficients.')
            d*=math.exp(factor)
        if inputs['exposure']=='immersion':
            if inputs.get('immersion_medium')!='water':
                raise ValueError('Ce modèle de diffusion traite l’eau ; sélectionnez Eau ou utilisez une loi spécifique au liquide.')
            activity=1.
        else:
            activity=(inputs['humidity_RH']/100)**_required(p,'sorption_exponent')
        uptake,integral=slab_uptake(t,d,float(inputs['thickness_mm']))
        water=activity*uptake
        effects.update(diffusivity_at_conditions_m2_s=d,water_activity=activity)
        if 'hydrolysis' in selected:
            rate=_arrhenius(p,'hydrolysis',temperature)
            damage+=rate*activity*integral; effects['hydrolysis_saturated_rate_day']=rate
    if 'stiffening' in selected:
        rate=_arrhenius(p,'stiffening',temperature)
        gain=1+_required(p,'stiffening_gain')*(-np.expm1(-rate*t))
        effects['stiffening_rate_at_conditions_day']=rate
    residual=_required(p,'residual_fraction') if {'thermal','uv','hydrolysis'} & set(selected) else 0.
    plastic=_required(p,'plasticization_fraction') if 'plasticization' in selected else 0.
    retention=(residual+(1-residual)*np.exp(-damage))*(1-plastic*water)*gain
    if not np.isfinite(retention).all(): raise ValueError('Calcul hors domaine numérique : vérifier les coefficients.')
    return retention,water,effects


def _crossing(evaluate,horizon,target):
    # Dense log+linear search resolves early water uptake as well as late loss.
    grid=np.unique(np.r_[0.,np.geomspace(max(horizon*1e-12,1e-12),horizon,1200),np.linspace(0,horizon,1201)])
    y=evaluate(grid)-target
    if target>=1: return 0.
    indexes=np.flatnonzero(y<=0)
    if not len(indexes): return None
    i=int(indexes[0])
    return float(brentq(lambda day:float(evaluate(np.array([day]))[0]-target),grid[i-1],grid[i]))


def apply_family_physics(result,material):
    plan=family_plan(material); result['manifest']['family_plan']=plan
    config=material.get('physics_model')
    if not config or not config.get('enabled'): return result
    validate_config(config)
    if not plan['supported']: raise ValueError('Famille non reconnue : renseignez une famille du catalogue ou le polymère de base.')
    inputs=result['manifest']['inputs']; temperature=float(inputs['temperature'])
    p={k:float(v) for k,v in config['parameters'].items() if v not in (None,'')}
    selected=list(dict.fromkeys(config['mechanisms']))
    if number(material.get('tm_c')) is not None and temperature>=float(material['tm_c']):
        raise ValueError('Température au-dessus de Tm : le modèle de matériau solide n’est pas applicable.')
    tg=number(material.get('tg_c')); reference=number(p.get('reference_temperature_c'))
    if tg is not None and reference is not None and (temperature-tg)*(reference-tg)<=0 and temperature!=reference:
        raise ValueError('Le transfert traverse Tg : une loi spécifique aux deux états est nécessaire.')
    horizon=inputs['horizon_years']*365.25
    days=np.unique(np.r_[np.linspace(0,horizon,241),np.geomspace(max(horizon*1e-8,1e-12),horizon,120)])
    ret,water,effects=_response(days,inputs,p,selected)
    evaluate=lambda t:_response(t,inputs,p,selected)[0]
    crossing=_crossing(evaluate,horizon,inputs['threshold']/100)
    scenarios=[ret]; bounds=config.get('bounds') or {}; keys=list(bounds)
    # Full factorial corners of supplied parameter ranges. These are scenarios,
    # not probabilities and not a guaranteed global envelope of a nonlinear law.
    for corner in itertools.product(*[bounds[k] for k in keys]) if keys else []:
        params={**p,**dict(zip(keys,corner))}
        corner_reference=number(params.get('reference_temperature_c'))
        if tg is not None and corner_reference is not None and (temperature-tg)*(corner_reference-tg)<=0 and temperature!=corner_reference:
            raise ValueError('Une borne traverse Tg : réduire la plage ou utiliser une loi adaptée.')
        scenarios.append(_response(days,inputs,params,selected)[0])
    low=np.min(scenarios,axis=0); high=np.max(scenarios,axis=0)
    e0=inputs['e0']; manifest=result['manifest']
    result.update(time=(days/365.25).tolist(),modulus=(e0*ret).tolist(),retention=(100*ret).tolist(),
                  lower=(e0*low).tolist(),upper=(e0*high).tolist(),
                  crossing=crossing/365.25 if crossing is not None else None,
                  crossing_estimate_years=crossing/365.25 if crossing is not None else None,
                  crossing_interval=[None,None],fraction_crossing=float(crossing is not None),rate=None)
    for key in ('outer_lower','outer_upper','observed_points'): result.pop(key,None)
    assumptions={'profile_method':'family_mechanistic','evidence_calibrated':False,
                 'evidence_window_days':None,'extrapolation_multiple':None,'validation':{},
                 'evidence_experiments':0,'independent_sources':0,'documentary_match':{'score':0,'label':'Coefficients fournis'},
                 'selected_mechanisms':selected,'parameter_source':str(config['source'])}
    manifest.update(model='datasheet-screening-family-physics-v1',engine_version=VERSION,
                    dataset='user-supplied-kinetics',assumptions=assumptions,
                    evidence_level='parameterised_research_model',
                    source={'title':'Coefficients fournis par l’utilisateur','location':str(config['source']),'sources':[]})
    manifest['family_physics']={'version':VERSION,'active':True,'family':plan,'parameters':p,
        'mechanisms':selected,'effects':effects,'source':str(config['source']),
        'bounds':bounds,'scenario_count':len(scenarios),'mean_water_fraction':water.tolist(),
        'formula':'E/E0 = [r + (1-r) exp(-dommage)] × [1-p·eau] × [1+g·(1-exp(-k_r·t))]',
        'references':REFERENCES,'precision_established':False}
    manifest['validity']={'temperature_c':[temperature,temperature], 'humidity_rh':[inputs['humidity_RH'],inputs['humidity_RH']],
        'exposure':inputs['exposure'],'material_scope':'Grade, milieu et coefficients déclarés ; domaine expérimental non établi.'}
    manifest['intended_use']='Prédiction de recherche conditionnelle aux coefficients, à figer puis confronter aux essais.'
    manifest['uncertainty']={'kind':'parameter_corner_sensitivity' if bounds else 'unquantified',
        'label':'Scénarios aux bornes des coefficients' if bounds else 'Incertitude non quantifiée',
        'display_band':bool(bounds),'predictive_interval_validated':False,
        'interpretation':'Sensibilité aux combinaisons extrêmes fournies ; aucune probabilité ni garantie de couverture.',
        'coverage':'Non mesurée','base_half_width_pct':None}
    manifest['warnings']=[
        'Coefficients déclarés : leur source et leur applicabilité au grade doivent être vérifiées.',
        'Modèle réduit : température, humidité et irradiation constantes ; pas de chargement mécanique.',
        'Le module est évalué dans le même état de mesure que E0 ; effet instantané de la température d’essai non calculé.',
        'Les effets couplés sont une hypothèse de modélisation, pas une calibration universelle.',
    ]
    if {'hydrolysis','plasticization'} & set(selected):
        manifest['warnings'].append('Plaque initialement sèche, eau pénétrant par deux faces, diffusion fickienne ; pas de consommation d’eau ni gonflement calculés.')
    if 'stiffening' in selected:
        manifest['warnings'].append('Une hausse de module n’exclut pas une fragilisation : la résistance et l’allongement ne sont pas prédits.')
    return result
