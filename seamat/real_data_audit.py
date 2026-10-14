"""Reproducible end-to-end checks against accepted laboratory observations."""
from __future__ import annotations

from io import BytesIO
import json
from zipfile import ZipFile

import numpy as np
from pypdf import PdfReader

from seamat import material_db
from seamat.blind_prediction import compare_with_experiment, freeze_prediction
from seamat.excel_reporting import result_workbook
from seamat.modeling import estimate_from_datasheet
from seamat.pdf_reporting import result_pdf
from seamat.reporting import markdown_report
from seamat.validation import iir_temperature_holdout, pp_literature_only_benchmark


def _estimate(material_id, e0, temperature, humidity, thickness, days, threshold,
              exposure, medium=None, tolerance=5., material=None):
    material=material or material_db.material(material_id)
    rows=material_db.evidence_rows(material_id,exposure)
    return estimate_from_datasheet(material,e0,temperature,humidity,thickness,days/365.25,
                                   threshold,exposure,rows,medium,
                                   precision_tolerance_pct=tolerance)


def _maximum_relative_difference(left, right):
    left=np.asarray(left,dtype=float); right=np.asarray(right,dtype=float)
    return float(np.max(np.abs(left-right)/np.maximum(np.abs(left),1e-12))*100)


def _iir_exact_reconstruction():
    rows=material_db.evidence_rows('IIR','immersion')
    details=[]
    for temperature in (80.,100.,120.):
        group=sorted((row for row in rows if float(row.get('ageing_temperature_c'))==temperature),
                     key=lambda row:float(row['time_days']))
        result=_estimate('IIR',float(group[0]['modulus_mpa']),temperature,50,2,1,70,
                         'immersion','milform64')
        predicted=np.interp([float(row['time_days']) for row in group],
                            np.asarray(result['time'])*365.25,result['modulus'])
        observed=np.asarray([float(row['modulus_mpa']) for row in group])
        errors=np.abs(predicted-observed)/observed*100
        details.append({
            'temperature_c':temperature,'points':len(group),
            'mape_pct':float(np.mean(errors)),'maximum_error_pct':float(np.max(errors)),
            'initial_mpa':float(observed[0]),'final_24h_mpa':float(observed[-1]),
        })
    return details


def _advanced_controls():
    pp1000=_estimate('PP',1000,23,50,2,120,80,'outdoor')
    pp2000=_estimate('PP',2000,23,50,2,120,80,'outdoor')
    pp85=_estimate('PP',1000,23,50,2,120,85,'outdoor')
    pp_tol2=_estimate('PP',1000,23,50,2,120,80,'outdoor',tolerance=2)
    pp_tol5=_estimate('PP',1000,23,50,2,120,80,'outdoor',tolerance=5)
    pp_thick=_estimate('PP',1000,23,50,8,120,80,'outdoor')
    iir_dry=_estimate('IIR',2.7,100,0,2,1,70,'immersion','milform64')
    iir_humid=_estimate('IIR',2.7,100,100,2,1,70,'immersion','milform64')
    iir80=_estimate('IIR',2.87,80,50,2,1,70,'immersion','milform64')
    iir100=_estimate('IIR',2.70,100,50,2,1,70,'immersion','milform64')

    water_config={'enabled':True,'source':'Contrôle numérique interne — coefficients de test, sans valeur probante',
                  'mechanisms':['hydrolysis','plasticization'],
                  'parameters':{'reference_temperature_c':23.,'residual_fraction':0.,
                                'diffusion_m2_s':1e-12,'diffusion_ea_kj_mol':25.,
                                'sorption_exponent':1.,'hydrolysis_rate_day':.01,
                                'hydrolysis_ea_kj_mol':40.,'plasticization_fraction':.2},
                  'bounds':{}}
    pa6={**material_db.material('PA6'),'physics_model':water_config}
    thin=_estimate('PA6',2500,23,100,1,20,80,'indoor',material=pa6)
    thick=_estimate('PA6',2500,23,100,4,20,80,'indoor',material=pa6)
    dry=_estimate('PA6',2500,23,0,1,20,80,'indoor',material=pa6)
    hot=_estimate('PA6',2500,43,100,1,20,80,'indoor',material=pa6)

    p2=pp_tol2['manifest']['precision']; p5=pp_tol5['manifest']['precision']
    thickness_check=next(check for check in pp_thick['manifest']['precision']['domain_checks']
                         if check['parameter']=='Épaisseur')
    return {
        'module_initial':{
            'expected':'La courbe en MPa est multipliée par 2, la rétention reste identique.',
            'module_ratio_at_horizon':float(pp2000['modulus'][-1]/pp1000['modulus'][-1]),
            'maximum_retention_difference_pct_point':float(np.max(np.abs(np.asarray(pp2000['retention'])-pp1000['retention']))),
            'passed':bool(np.allclose(np.asarray(pp2000['modulus']),2*np.asarray(pp1000['modulus']))),
        },
        'threshold':{
            'expected':'Le seuil change le temps de franchissement, jamais la courbe physique.',
            'maximum_curve_difference_pct':_maximum_relative_difference(pp1000['modulus'],pp85['modulus']),
            'crossing_80_years':pp1000['crossing_estimate_years'],
            'crossing_85_years':pp85['crossing_estimate_years'],
            'passed':bool(np.allclose(pp1000['modulus'],pp85['modulus']) and pp85['crossing_estimate_years']<pp1000['crossing_estimate_years']),
        },
        'precision_tolerance':{
            'expected':'La tolérance change le score de validation, jamais la courbe.',
            'precision_at_2_pct':p2['reference_precision_pct'],
            'precision_at_5_pct':p5['reference_precision_pct'],
            'maximum_curve_difference_pct':_maximum_relative_difference(pp_tol2['modulus'],pp_tol5['modulus']),
            'passed':bool(p2['reference_precision_pct']<p5['reference_precision_pct'] and np.allclose(pp_tol2['modulus'],pp_tol5['modulus'])),
        },
        'immersion_humidity':{
            'expected':'L’humidité de l’air est sans objet en immersion.',
            'maximum_curve_difference_pct':_maximum_relative_difference(iir_dry['modulus'],iir_humid['modulus']),
            'passed':bool(np.allclose(iir_dry['modulus'],iir_humid['modulus'])),
        },
        'source_based_thickness':{
            'expected':'Aucun effet ne doit être inventé quand la publication ne caractérise pas l’épaisseur.',
            'maximum_curve_difference_pct':_maximum_relative_difference(pp1000['modulus'],pp_thick['modulus']),
            'domain_status':thickness_check['status'],'domain_detail':thickness_check['detail'],
            'passed':bool(np.allclose(pp1000['modulus'],pp_thick['modulus']) and not thickness_check['compatible']),
        },
        'published_temperature':{
            'expected':'Les courbes IIR publiées à 80 et 100 °C restent distinctes.',
            'retention_24h_80c_pct':float(iir80['retention'][-1]),
            'retention_24h_100c_pct':float(iir100['retention'][-1]),
            'passed':bool(not np.allclose(iir80['retention'],iir100['retention'])),
        },
        'mechanism_temperature_humidity_thickness':{
            'expected':'Avec des coefficients explicites, température, humidité et épaisseur pilotent la diffusion et l’hydrolyse.',
            'retention_20d_thin_pct':float(thin['retention'][-1]),
            'retention_20d_thick_pct':float(thick['retention'][-1]),
            'retention_20d_dry_pct':float(dry['retention'][-1]),
            'retention_20d_hot_pct':float(hot['retention'][-1]),
            'coefficient_status':'contrôle numérique, pas validation expérimentale',
            'passed':bool(thin['retention'][-1]<thick['retention'][-1]<dry['retention'][-1]
                          and hot['retention'][-1]<thin['retention'][-1]),
        },
        'uniform_visible_band':{
            'expected':'Toutes les projections de fiche utilisent ×0,95/×1,05 sur la vitesse ; la bande scientifique reste exportée.',
            'kind':pp1000['manifest']['uncertainty']['kind'],
            'rate_multipliers':pp1000['manifest']['uncertainty']['rate_multipliers'],
            'source_specific_kind':pp1000['manifest']['uncertainty']['source_specific']['kind'],
            'passed':bool(pp1000['manifest']['uncertainty']['kind']=='standardized_rate_sensitivity'),
        },
    },pp1000,iir100


def _export_checks(pp_result, iir_result):
    xlsx=result_workbook(pp_result,'Audit PP · données réelles')
    archive=ZipFile(BytesIO(xlsx)); names=set(archive.namelist())
    shared=archive.read('xl/sharedStrings.xml').decode('utf-8')
    pdf=result_pdf(pp_result,'Audit PP · données réelles')
    markdown=markdown_report(pp_result,'Audit PP · données réelles')
    snapshot=freeze_prediction(iir_result,'IIR 100 °C · comparaison avec le tableau publié','2024-01-01')
    real_rows=sorted((row for row in material_db.evidence_rows('IIR','immersion')
                      if float(row.get('ageing_temperature_c'))==100.),key=lambda row:float(row['time_days']))
    observations=[{'time_days':float(row['time_days']),'modulus_mpa':float(row['modulus_mpa']),
                   'replicate_id':f"table-{index+1}",'lot_id':'publication','specimen_id':f"table-{index+1}"}
                  for index,row in enumerate(real_rows)]
    comparison=compare_with_experiment(snapshot,observations)
    checks={
        'xlsx':bool(xlsx.startswith(b'PK') and 'xl/charts/chart1.xml' in names
                    and '10.3390/polym16131788' in shared and 'Mesures source' in shared),
        'pdf':bool(pdf.startswith(b'%PDF') and len(PdfReader(BytesIO(pdf)).pages)>=2),
        'markdown':bool(markdown.startswith(b'# ') and b'Empreinte' in markdown),
        'json':bool(json.loads(json.dumps(pp_result,ensure_ascii=False,allow_nan=False))['fingerprint']==pp_result['fingerprint']),
        'frozen_real_data_comparison':bool(comparison['count']==7 and comparison['mape_pct']<1e-9),
    }
    return {
        'checks':checks,'all_passed':all(checks.values()),
        'xlsx_bytes':len(xlsx),'pdf_bytes':len(pdf),'markdown_bytes':len(markdown),
        'iir_100c_real_points':comparison['count'],
        'iir_100c_exported_comparison_mape_pct':comparison['mape_pct'],
        'iir_100c_interval_coverage_pct':comparison['interval_coverage_pct'],
    }


def real_data_audit():
    """Run the release audit and return a JSON-safe, source-traceable report."""
    pp_rows=material_db.evidence_rows('PP','outdoor')
    pp=pp_literature_only_benchmark(pp_rows)
    iir_exact=_iir_exact_reconstruction()
    iir_transfer=iir_temperature_holdout(material_db.evidence_rows('IIR','immersion'))
    controls,pp_result,iir_result=_advanced_controls()
    exports=_export_checks(pp_result,iir_result)
    controls_passed=all(item['passed'] for item in controls.values())
    exact_passed=all(item['maximum_error_pct']<1e-9 for item in iir_exact)
    release_checks=bool(pp['mape_pct']<5 and exact_passed and controls_passed and exports['all_passed'])
    return {
        'audit_version':'seamat-real-data-e2e-1.0.0',
        'status':'CONTRÔLES FONCTIONNELS RÉUSSIS' if release_checks else 'ÉCHEC DE CONTRÔLE',
        'release_checks_passed':release_checks,
        'scientific_scope':'Validation interne sur PP H301 et restitution IIR ; aucune validation universelle de tous les grades.',
        'real_cases':{
            'pp_leave_one_formulation_out':{
                'source_doi':'10.3390/polym16131788','test_predictions':pp['test_count'],
                'mape_pct':pp['mape_pct'],'maximum_error_pct':pp['max_relative_error_pct'],
                'empirical_coverage_pct':pp['empirical_coverage_pct'],
                'conclusion':pp['conclusion'],
            },
            'iir_exact_published_curves':{
                'source_doi':'10.3390/jcs3020048','details':iir_exact,
                'interpretation':'Restitution des points du tableau par interpolation ; ce n’est pas un test prédictif externe.'
            },
            'iir_hidden_temperature_transfer':{
                'source_doi':'10.3390/jcs3020048','test_predictions':iir_transfer['test_count'],
                'mape_pct':iir_transfer['mape_pct'],'maximum_error_pct':iir_transfer['max_relative_error_pct'],
                'r2':iir_transfer['r2'],'status':iir_transfer['status'],
                'interpretation':'Le transfert de température reste refusé comme modèle qualifié ; le logiciel ne masque pas cet échec.'
            },
        },
        'advanced_parameter_controls':controls,
        'exports_and_extracted_data':exports,
        'sources':[
            {'title':'Natural Aging of Reprocessed Polypropylene Composites Filled with Sustainable Corn Fibers',
             'doi':'10.3390/polym16131788','url':'https://www.mdpi.com/2073-4360/16/13/1788'},
            {'title':'Butyl Rubber-Based Composite: Thermal Degradation and Prediction of Service Lifetime',
             'doi':'10.3390/jcs3020048','url':'https://www.mdpi.com/2504-477X/3/2/48'},
        ],
    }
