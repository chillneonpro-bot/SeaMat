"""Numerical unit fixtures are synthetic; no fixture enters the literature DB."""
import copy
import math
import json
import zipfile
import io

import numpy as np
import pytest

from seamat import material_db
from seamat.hybrid_engine import fit_environment_expert, apply_environment_expert, validate_descriptors
from seamat.modeling import estimate_from_datasheet, standard_profile
from seamat.reliability import _coverage_95_claim
from seamat.excel_reporting import result_workbook


def synthetic_arrhenius():
    rows = []
    for grade in ('A', 'B', 'C'):
        for temperature in (23., 43., 63.):
            rate = .001 * math.exp(40000 / 8.314462618 * (1/296.15 - 1/(temperature+273.15)))
            for day in (0., 10., 20., 40.):
                rows.append(dict(source_id='synthetic-unit-fixture', experiment_id=f'{grade}-{temperature}',
                                 grade_id=grade, time_days=day, modulus_mpa=1000*math.exp(-rate*day),
                                 ageing_temperature_c=temperature, humidity_rh=50., thickness_mm=2.,
                                 evidence_status='accepted_scientific_review'))
    return rows


def pp(days=120, tolerance=5, descriptors=None):
    material={**material_db.material('PP'), **(descriptors or {})}
    return estimate_from_datasheet(material,1100,23,50,2,days/365.25,80,'outdoor',
                                   material_db.model_evidence_rows('PP','outdoor'),
                                   precision_tolerance_pct=tolerance)


def test_arrhenius_is_identified_without_using_the_hidden_grade():
    rows=synthetic_arrhenius()
    audit=fit_environment_expert(rows,dict(temperature_c=43,humidity_rh=50,thickness_mm=2))
    assert audit['active']
    assert audit['validation_protocol']=='leave_one_grade_out'
    assert audit['features']==['temperature_c']
    assert audit['activation_energy_kj_mol']==pytest.approx(40,abs=1e-8)
    assert audit['validation']['test_predictions']==27
    assert audit['validation']['mape_pct']<1e-9
    hot=fit_environment_expert(rows,dict(temperature_c=63))
    assert hot['rate_per_day']>audit['rate_per_day']
    assert not fit_environment_expert(rows,dict(temperature_c=70))['active']
    assert not fit_environment_expert(rows,{})['active']


def test_confounded_effects_and_unseen_response_shapes_are_not_silently_accepted():
    rows=synthetic_arrhenius()
    for row in rows: row['thickness_mm']=math.exp(1000*(1/296.15-1/(row['ageing_temperature_c']+273.15)))
    assert not fit_environment_expert(rows,dict(temperature_c=43,thickness_mm=rows[4]['thickness_mm']))['active']
    rows=synthetic_arrhenius()
    rows += [{**r,'grade_id':'D','experiment_id':r['experiment_id'].replace('A-','D-')}
             for r in rows if r['grade_id']=='A']
    for row in rows:
        if row['grade_id']=='C': row['modulus_mpa']=1000*(1+row['time_days']/40)
    rejected=fit_environment_expert(rows,dict(temperature_c=43))
    assert not rejected['active']
    assert rejected['validation']['max_ape_pct']>20
    assert any(p['group']=='C' for p in rejected['predictions'])


def test_wrong_property_and_invalid_temperature_cannot_train():
    rows=synthetic_arrhenius()
    for row in rows: row['property_name']='Résistance à la traction'
    assert not fit_environment_expert(rows,dict(temperature_c=43))['active']
    rows=synthetic_arrhenius()
    for row in rows: row['ageing_temperature_c']=-273.15
    assert not fit_environment_expert(rows,dict(temperature_c=43))['active']


def test_active_expert_updates_curve_threshold_and_manifest_together():
    audit=fit_environment_expert(synthetic_arrhenius(),dict(temperature_c=43))
    result=apply_environment_expert(pp(40),audit)
    days=np.array(result['time'])*365.25
    assert np.allclose(result['modulus'],1100*np.exp(-audit['rate_per_day']*days))
    assert result['upper'][0]==result['lower'][0]==1100
    assert all(lo<=mid<=hi for lo,mid,hi in zip(result['lower'],result['modulus'],result['upper']))
    crossing=-math.log(.8)/audit['rate_per_day']/365.25
    assert result['crossing_estimate_years']==pytest.approx(crossing)
    assert result['manifest']['assumptions']['profile_method']=='learned_environment_kinetics'
    json.dumps(result,allow_nan=False)


def test_precision_is_measured_and_description_cannot_inflate_it():
    result=pp(); quality=result['manifest']['precision']
    assert quality['reference_precision_pct']==100
    assert quality['prediction_count']==8 and quality['group_count']==4
    assert quality['mean_relative_error_pct']==pytest.approx(2.749835655,abs=1e-7)
    assert quality['target_precision_pct'] is None
    more=pp(descriptors={'density_kg_m3':900,'tg_c':-10,'crystallinity_pct':40})['manifest']['precision']
    assert more['completeness_pct']>quality['completeness_pct']
    assert more['reference_precision_pct']==quality['reference_precision_pct']
    assert more['target_precision_pct'] is None
    assert result['fingerprint']!=pp(descriptors={'density_kg_m3':900})['fingerprint']
    assert pp(30)['manifest']['precision']['prediction_count']==4
    assert pp(tolerance=2)['manifest']['precision']['reference_precision_pct']<100
    assert pp(365)['manifest']['precision']['target_precision_pct'] is None


def test_absent_benchmark_does_not_produce_zero_or_invent_accuracy():
    mat=material_db.material('PEEK')
    result=estimate_from_datasheet(mat,standard_profile(mat)['suggested_modulus_mpa'],23,50,2,1,80)
    quality=result['manifest']['precision']
    assert quality['reference_precision_pct'] is None
    assert quality['prediction_count']==0
    assert quality['target_precision_pct'] is None


@pytest.mark.parametrize('value',[-1,float('nan'),float('inf'),'incorrect'])
def test_invalid_descriptors_fail_before_calculation(value):
    with pytest.raises(ValueError): validate_descriptors({'density_kg_m3':value})


def test_internal_cross_validation_never_counts_as_external_95_evidence():
    internal={'independent_validation_groups':100,'covered_validation_groups':100,
              'validation_design':'internal_group_cross_validation'}
    report=_coverage_95_claim(internal,10)
    assert report['qualified'] is False
    assert report['one_sided_lower_bound_pct'] is None


def test_workbook_contains_auditable_precision_and_hidden_predictions():
    workbook=result_workbook(pp(),'Précision PP')
    with zipfile.ZipFile(io.BytesIO(workbook)) as archive:
        assert 'Précision et paramètres' in archive.read('xl/workbook.xml').decode()
        strings=archive.read('xl/sharedStrings.xml').decode()
        assert 'Votre grade' in strings and 'Non caractérisé' in strings


def test_full_catalogue_returns_finite_curves_and_explicit_quality():
    for mat in material_db.catalog():
        result=estimate_from_datasheet(mat,standard_profile(mat)['suggested_modulus_mpa'],23,50,2,1,80,
                                       evidence_rows=material_db.model_evidence_rows(mat['id'],'indoor'))
        assert np.isfinite(result['modulus']).all(), mat['id']
        assert 'target_precision_pct' in result['manifest']['precision']
        json.dumps(result,allow_nan=False)
