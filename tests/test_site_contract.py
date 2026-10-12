import pytest
from fastapi import HTTPException

import main
from seamat import __version__
from seamat.engine_v2 import ENGINE_VERSION


def test_french_number_format_uses_unambiguous_separators():
    assert main.number_fr(1502) == '1\u202f502'
    assert main.number_fr(48.5, 1) == '48,5'
    with pytest.raises(ValueError):
        main.number_fr(float('nan'))


def test_unknown_material_api_uses_http_404():
    with pytest.raises(HTTPException) as error:
        main.material_api('not-a-material')
    assert error.value.status_code == 404
    assert error.value.detail['material_id'] == 'not-a-material'


def test_material_api_is_case_insensitive():
    response = main.material_api('pp')
    assert response['material']['id'] == 'PP'
    assert 'scientific_audit' in response


def test_health_uses_the_package_version():
    assert main.health()['version'] == __version__
    assert main.health()['engine_version'] == ENGINE_VERSION


def test_v2_benchmark_exposes_reproducible_real_evidence_cases():
    report=main.v2_benchmark_api()
    assert report['engine_version']==ENGINE_VERSION
    assert report['pp_23c_120d']['hidden_predictions']==8
    assert report['pp_23c_120d']['hidden_mape_pct']==pytest.approx(2.7498356554)
    assert report['pp_23c_120d']['prediction_half_width_pct']==pytest.approx(3.411,abs=.001)
    assert report['iir_exact_100c_24h']['route']=='exact_temperature_curve'
    assert report['iir_transfer_90c_24h']['route']=='temperature_surface_interpolation'
    assert (report['iir_transfer_90c_24h']['prediction_half_width_pct']>
            report['iir_exact_100c_24h']['prediction_half_width_pct'])
    assert 'INSUFFISANTE' in report['iir_transfer_90c_24h']['status']
