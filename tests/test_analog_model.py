import pytest

from seamat.analog_model import MIN_ANALOG_SCORE, rank_analogs
from seamat.modeling import estimate_from_datasheet


def custom_pp(**overrides):
    material={
        'id':'CUSTOM-PP','name':'PP recyclé','abbreviation':'R-PP',
        'family':'Polyoléfine','base_polymer':'PP',
        'mechanisms':'Photo-oxydation; thermo-oxydation',
        'suggested_modulus_mpa':1200.,'process_state':'Injection',
        'reinforcement':'Aucun','reinforcement_pct':0,
        'service_exposure':'outdoor','custom':True,
    }
    material.update(overrides)
    return material


def estimate(material,days=120):
    return estimate_from_datasheet(material,float(material['suggested_modulus_mpa']),23,50,2,
                                   days/365.25,80,'outdoor',[],None,
                                   material.get('grade_reference'),material.get('process_state'))


def test_close_manual_pp_uses_auditable_analogue_inside_published_window():
    candidates=rank_analogs(custom_pp(),'outdoor')
    assert candidates[0]['material_id']=='PP'
    assert candidates[0]['score']>=MIN_ANALOG_SCORE
    result=estimate(custom_pp())
    transfer=result['manifest']['assumptions']['analog_transfer']
    assert result['manifest']['model']=='datasheet-analog-transfer-v1'
    assert transfer['source_material_id']=='PP'
    assert transfer['similarity_score']==candidates[0]['score']
    assert result['manifest']['reliability']['code']=='analog_supported_limited'
    assert result['manifest']['reliability']['usable_for_screening'] is True
    assert result['manifest']['reliability']['qualified_external'] is False
    # The module at 120 days is usable; an 80 % crossing beyond that published
    # window is deliberately not returned as a qualified lifetime.
    assert result['crossing_estimate_years'] is None
    assert transfer['threshold_within_evidence'] is False


def test_custom_grade_preserves_time_units_and_cannot_borrow_target_accuracy():
    from seamat.charts import curve, _comparison_time_days
    from seamat.excel_reporting import _time_days, _display_axis
    from seamat.modeling import curve_value_origin
    result=estimate(custom_pp())
    assert _time_days(result)[-1]==pytest.approx(120)
    assert _comparison_time_days(result)[-1]==pytest.approx(120)
    assert _display_axis(result)[1]=='années'
    assert 'années' in curve(result).layout.xaxis.title.text
    assert 'analogue' in curve_value_origin(result)
    precision=result['manifest']['precision']
    assert precision['reference_precision_pct']==100
    assert precision['target_precision_pct'] is None
    assert precision['external_qualified'] is False


def test_analogue_transfer_adds_uncertainty_to_the_source_model():
    result=estimate(custom_pp())
    uncertainty=result['manifest']['uncertainty']
    source=uncertainty['source_specific']
    assert uncertainty['kind']=='standardized_rate_sensitivity'
    assert source['kind']=='source_calibration_plus_analogue_penalty'
    assert source['base_half_width_pct']>source['source_specific']['base_half_width_pct']
    assert all(low<center<high for low,center,high in
               zip(result['lower'][1:],result['modulus'][1:],result['upper'][1:]))


def test_vague_manual_material_cannot_borrow_an_unrelated_curve():
    material=custom_pp(name='Polymère X',abbreviation='X',family='Inconnue',base_polymer='',
                       mechanisms='Non renseigné',process_state='')
    assert rank_analogs(material,'outdoor')[0]['score']<MIN_ANALOG_SCORE
    result=estimate(material)
    assert result['manifest']['model']!='datasheet-analog-transfer-v1'
    assert result['manifest']['reliability']['code']=='documentary_only'
    assert result['manifest']['reliability']['usable_for_screening'] is False


def test_close_analogue_is_not_qualified_beyond_its_published_window():
    result=estimate(custom_pp(),365)
    assert result['manifest']['reliability']['code']=='analog_extrapolation_unqualified'
    assert result['manifest']['reliability']['usable_for_screening'] is False


def test_reinforced_custom_grade_is_penalized_when_source_is_unreinforced():
    material=custom_pp(reinforcement='Fibres de verre',reinforcement_pct=30)
    candidates=rank_analogs(material,'outdoor')
    assert candidates[0]['score']<MIN_ANALOG_SCORE
    assert any('renfort' in limit for limit in candidates[0]['limits'])
