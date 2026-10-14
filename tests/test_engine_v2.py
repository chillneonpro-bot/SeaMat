import numpy as np
import pytest

from seamat import material_db
from seamat.engine_v2 import (ENGINE_VERSION, Request, capability_summary,
                              evidence_quality, predict_from_evidence,
                              select_kinetic_model)


def request(material_id='PP', temperature=23, horizon=120, exposure='outdoor', medium=None):
    return Request(material_id=material_id,material_name=material_id,modulus_mpa=1000,
                   temperature_c=temperature,humidity_rh=50,thickness_mm=2,
                   horizon_days=horizon,threshold_percent=80,exposure=exposure,
                   immersion_medium=medium)


def test_control_1_data_contract_rejects_invalid_rows():
    audit=evidence_quality([{'experiment_id':'A','time_days':-1,'modulus_mpa':0,'source_id':'S'}])
    assert audit['status']=='insufficient'
    assert audit['issues']


def test_control_2_pp_units_and_rows_are_usable():
    audit=evidence_quality(material_db.evidence_rows('PP','outdoor'))
    assert audit['status']=='usable'
    assert audit['rows_valid']==22
    assert audit['independent_sources']==3


def test_reviewed_import_schema_is_normalized_for_any_new_material():
    rows=[]
    for experiment,temperature in (("A",40),("B",50),("C",60)):
        for day,value in ((0,2000),(10,1800),(20,1600)):
            rows.append({'experiment_id':experiment,'time_days':day,'modulus_MPa':value,
                         'temperature_C':temperature,'humidity_RH':50,'thickness_mm':2,
                         'source_id':'reviewed-source','review_status':'accepted'})
    audit=evidence_quality(rows)
    assert audit['status']=='usable'
    assert audit['rows_valid']==9


def test_control_3_multimodel_selector_returns_auditable_candidates():
    chosen=select_kinetic_model(np.array([0.,30.,120.]),np.array([1.,.92,.90]))
    assert chosen['name'] in {'exponential','weibull','plateau_exponential'}
    assert {item['name'] for item in chosen['candidates']}=={'exponential','weibull','plateau_exponential'}


def test_controls_4_to_6_route_pp_and_record_domain_match():
    result=predict_from_evidence(request(),material_db.evidence_rows('PP','outdoor'))
    assert result is not None
    assumptions=result['manifest']['assumptions']
    assert assumptions['profile_method']=='same_material_ensemble'
    assert assumptions['documentary_match']['probability'] is False
    assert result['manifest']['validity']['time_days']==[0,120]


def test_control_7_pp_band_is_calibrated_on_hidden_formulations():
    result=predict_from_evidence(request(),material_db.evidence_rows('PP','outdoor'))
    uncertainty=result['manifest']['uncertainty']
    assert uncertainty['kind']=='empirical_group_residuals'
    assert uncertainty['base_half_width_pct']==pytest.approx(3.4109767496)
    assert uncertainty['target_coverage_pct']==95
    assert uncertainty['calibration']['empirical_point_coverage_pct']==100
    assert uncertainty['calibration']['independent_validation_groups']==4
    assert uncertainty['calibration']['covered_validation_groups']==4


def test_control_8_validation_recovers_published_pp_error():
    result=predict_from_evidence(request(),material_db.evidence_rows('PP','outdoor'))
    validation=result['manifest']['assumptions']['validation']
    assert validation['test_predictions']==8
    assert validation['mape_pct']==pytest.approx(2.7498356554)
    assert validation['max_ape_pct']==pytest.approx(3.4109767496)


def test_exact_iir_curve_and_unmeasured_temperature_are_not_confused():
    rows=material_db.evidence_rows('IIR','immersion')
    exact=predict_from_evidence(request('IIR',100,1,'immersion','milform64'),rows)
    transfer=predict_from_evidence(request('IIR',90,1,'immersion','milform64'),rows)
    assert exact['manifest']['assumptions']['profile_method']=='exact_temperature_curve'
    assert transfer['manifest']['assumptions']['profile_method']=='temperature_surface_interpolation'
    assert transfer['manifest']['uncertainty']['base_half_width_pct']>exact['manifest']['uncertainty']['base_half_width_pct']
    assert transfer['manifest']['assumptions']['validation_passed'] is False
    assert 'INSUFFISANTE' in transfer['manifest']['status']


def test_exact_iir_threshold_is_found_inside_the_24_hour_window():
    rows=material_db.evidence_rows('IIR','immersion')
    result=predict_from_evidence(request('IIR',100,1,'immersion','milform64'),rows)
    crossing_days=result['crossing_estimate_years']*365.25
    assert 0 < crossing_days < 1
    assert result['crossing']==pytest.approx(result['crossing_estimate_years'])


def test_extrapolation_band_expands_beyond_observations():
    rows=material_db.evidence_rows('PP','outdoor')
    short=predict_from_evidence(request(horizon=120),rows)
    long=predict_from_evidence(request(horizon=1200),rows)
    short_width=(short['upper'][-1]-short['lower'][-1])/short['modulus'][-1]
    long_width=(long['upper'][-1]-long['lower'][-1])/long['modulus'][-1]
    assert long_width>short_width
    assert short['manifest']['uncertainty']['predictive_interval_validated'] is False
    assert long['manifest']['uncertainty']['predictive_interval_validated'] is False


def test_control_9_result_is_versioned_and_reproducible():
    rows=material_db.evidence_rows('PP','outdoor')
    first=predict_from_evidence(request(),rows)
    second=predict_from_evidence(request(),rows)
    assert first['manifest']['engine_version']==ENGINE_VERSION
    assert first['fingerprint']==second['fingerprint']


def test_control_10_capability_summary_exposes_all_controls():
    summary=capability_summary(material_db.evidence_rows('PP','outdoor'))
    assert summary['engine_version']==ENGINE_VERSION
    assert [item['id'] for item in summary['controls']]==list(range(1,11))
