"""Release tests that use the accepted published values, not generated fixtures."""
import pytest

import main
from seamat.real_data_audit import real_data_audit


@pytest.fixture(scope='module')
def audit():
    return real_data_audit()


def test_real_pp_and_iir_cases_are_reproduced_and_limits_are_visible(audit):
    assert audit['release_checks_passed'] is True
    pp=audit['real_cases']['pp_leave_one_formulation_out']
    assert pp['test_predictions']==8
    assert pp['mape_pct']==pytest.approx(2.7498356554)
    assert pp['maximum_error_pct']==pytest.approx(3.4109767496)
    assert pp['empirical_coverage_pct']==100
    assert all(row['maximum_error_pct']<1e-9
               for row in audit['real_cases']['iir_exact_published_curves']['details'])
    transfer=audit['real_cases']['iir_hidden_temperature_transfer']
    assert transfer['mape_pct']==pytest.approx(11.3127887737)
    assert transfer['maximum_error_pct']==pytest.approx(28.7630553980)
    assert 'NON VALIDÉ' in transfer['status']


def test_every_advanced_control_has_an_observable_or_explicitly_blocked_effect(audit):
    controls=audit['advanced_parameter_controls']
    assert controls and all(item['passed'] for item in controls.values())
    assert controls['module_initial']['module_ratio_at_horizon']==pytest.approx(2)
    assert controls['threshold']['maximum_curve_difference_pct']==pytest.approx(0)
    assert controls['threshold']['crossing_85_years']<controls['threshold']['crossing_80_years']
    assert controls['precision_tolerance']['precision_at_2_pct']==0
    assert controls['precision_tolerance']['precision_at_5_pct']==100
    assert controls['immersion_humidity']['maximum_curve_difference_pct']==pytest.approx(0)
    assert controls['source_based_thickness']['domain_status']=='Non caractérisé'
    assert controls['mechanism_temperature_humidity_thickness']['coefficient_status'].startswith('contrôle numérique')
    assert controls['uniform_visible_band']['rate_multipliers']==[.95,1.05]
    assert controls['uniform_visible_band']['source_specific_kind']=='empirical_group_residuals'


def test_exports_and_real_measurement_roundtrip_are_usable(audit):
    exported=audit['exports_and_extracted_data']
    assert exported['all_passed'] is True
    assert all(exported['checks'].values())
    assert exported['iir_100c_real_points']==7
    assert exported['iir_100c_exported_comparison_mape_pct']<1e-9
    assert exported['xlsx_bytes']>10_000 and exported['pdf_bytes']>5_000


def test_public_audit_endpoint_returns_the_same_contract():
    response=main.v3_real_data_audit_api()
    assert response['audit_version']=='seamat-real-data-e2e-1.0.0'
    assert response['release_checks_passed'] is True
