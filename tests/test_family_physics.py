"""Analytical checks use declared synthetic coefficients, never literature data."""
import copy
import io
import json
import math
import numpy as np
import pytest
from pypdf import PdfReader

from seamat import material_db
from seamat.family_physics import family_plan, slab_uptake, validate_config
from seamat.modeling import estimate_from_datasheet, sampled_curve_rows
from seamat.charts import curve
from seamat.excel_reporting import result_workbook
from seamat.pdf_reporting import result_pdf
from seamat.reporting import markdown_report
from seamat.blind_prediction import freeze_prediction


def config(mechanisms=None, **values):
    return {'enabled':True,'source':'Hypothèse synthétique de test — pas une donnée expérimentale',
            'mechanisms':mechanisms or ['thermal'],
            'parameters':{'reference_temperature_c':23.,'residual_fraction':0.,
                          'thermal_rate_day':.01,'thermal_ea_kj_mol':40.,**values},'bounds':{}}


def calculate(conf=None, material='PP', temperature=23., humidity=50., thickness=2., days=120.,
              exposure='indoor', medium=None, **properties):
    mat={**material_db.material(material),**properties,'physics_model':conf or config()}
    return estimate_from_datasheet(mat,1000,temperature,humidity,thickness,days/365.25,80,exposure,
                                   material_db.model_evidence_rows(material,exposure),medium)


def test_every_catalogue_family_is_recognised_without_inventing_coefficients():
    for mat in material_db.catalog():
        plan=family_plan(mat)
        assert plan['supported'],mat['family']
        assert plan['candidate_mechanisms']
        result=calculate(material=mat['id'])
        assert result['modulus'][-1]==pytest.approx(1000*math.exp(-1.2)),mat['id']
        assert result['manifest']['precision']['reference_precision_pct'] is None
    assert not family_plan({'family':'Unobtainium'})['supported']
    assert family_plan({'family':'Mon PP','base_polymer':'PP'})['resolved_from_base']=='PP'


def test_exponential_limit_threshold_and_arrhenius_recovery():
    result=calculate()
    t=np.array(result['time'])*365.25
    assert np.allclose(result['modulus'],1000*np.exp(-.01*t))
    assert result['modulus'][0]==1000
    assert result['crossing']*365.25==pytest.approx(-math.log(.8)/.01)
    hot=calculate(temperature=43.)
    k=.01*math.exp(40000/8.314462618*(1/296.15-1/316.15))
    assert hot['modulus'][-1]==pytest.approx(1000*math.exp(-k*120))
    assert hot['modulus'][-1]<result['modulus'][-1]


def test_plate_diffusion_matches_scaling_and_saturation():
    t=np.array([0.,.000001,.1,1.,10.,1000.])
    u,integral=slab_uptake(t,1e-12,2)
    assert u[0]==integral[0]==0
    assert np.all(np.diff(u)>=0) and np.all(integral<=t)
    assert u[-1]==pytest.approx(1)
    thick,thick_integral=slab_uptake(t*4,1e-12,4)
    assert np.allclose(u,thick)
    assert np.allclose(integral*4,thick_integral)
    grid=np.linspace(0,100,10001)
    uptake,area=slab_uptake(grid,1e-12,2)
    assert np.trapezoid(uptake,grid)==pytest.approx(area[-1],rel=2e-5)


def water_config():
    return config(['hydrolysis','plasticization'],diffusion_m2_s=1e-12,diffusion_ea_kj_mol=25,
                  hydrolysis_rate_day=.01,hydrolysis_ea_kj_mol=40,
                  plasticization_fraction=.2,sorption_exponent=1.)


def test_water_uses_thickness_humidity_and_liquid_not_an_arbitrary_factor():
    thin=calculate(water_config(),material='PA6',thickness=1,exposure='immersion',medium='water',days=20)
    thick=calculate(water_config(),material='PA6',thickness=4,exposure='immersion',medium='water',days=20)
    assert thin['modulus'][-1]<thick['modulus'][-1]
    same=calculate(water_config(),material='PA6',thickness=1,humidity=0,exposure='immersion',medium='water',days=20)
    assert same['modulus']==thin['modulus']
    dry=calculate(water_config(),material='PA6',humidity=0,days=20)
    humid=calculate(water_config(),material='PA6',humidity=100,days=20)
    assert dry['modulus'][-1]==1000
    assert humid['modulus'][-1]<dry['modulus'][-1]
    with pytest.raises(ValueError,match='traite l’eau'):
        calculate(water_config(),exposure='immersion',medium='milform64')


def test_uv_intensity_zero_and_reciprocity_are_explicit():
    c=config(['uv'],uv_rate_day=.01,uv_reference_w_m2=50,uv_irradiance_w_m2=50,uv_exponent=1)
    normal=calculate(c)
    c['parameters']['uv_irradiance_w_m2']=100
    double=calculate(c)
    assert double['retention'][-1]/100==pytest.approx((normal['retention'][-1]/100)**2)
    c['parameters']['uv_irradiance_w_m2']=0
    assert calculate(c)['modulus'][-1]==1000


def test_rigidification_can_increase_modulus_and_compete_with_damage():
    c=config(['stiffening'],stiffening_rate_day=.1,stiffening_gain=.5)
    pure=calculate(c)
    assert pure['modulus'][-1]>1400
    assert pure['crossing'] is None
    c['mechanisms']=['stiffening','thermal']
    mixed=calculate(c)
    assert max(mixed['modulus'])>1000 and mixed['modulus'][-1]<800
    assert mixed['crossing'] is not None


def test_resistant_fraction_prevents_unreachable_threshold_and_no_fake_band():
    result=calculate(config(residual_fraction=.9))
    assert result['crossing'] is None
    assert result['manifest']['uncertainty']['display_band'] is False
    assert result['lower']==result['upper']==result['modulus']


def test_corner_sensitivity_is_explicit_and_reproducible():
    c=config(); c['bounds']={'thermal_rate_day':[.005,.02]}
    result=calculate(c)
    assert result['manifest']['family_physics']['scenario_count']==3
    assert result['lower'][-1]==pytest.approx(1000*math.exp(-.02*120))
    assert result['upper'][-1]==pytest.approx(1000*math.exp(-.005*120))
    assert result['manifest']['uncertainty']['predictive_interval_validated'] is False
    assert result['fingerprint']==calculate(c)['fingerprint']


def test_missing_parameters_and_phase_changes_have_actionable_errors():
    c=config(); del c['parameters']['thermal_ea_kj_mol']
    with pytest.raises(ValueError,match='Énergie d’activation'): calculate(c,temperature=43)
    with pytest.raises(ValueError,match='Tm'): calculate(tm_c=20)
    with pytest.raises(ValueError,match='Tg'): calculate(temperature=50,tg_c=40)
    c=config(); c['parameters']['thermal_rate_day']=float('nan')
    with pytest.raises(ValueError,match='finie'): calculate(c)
    c=config(); c['bounds']={'thermal_rate_day':[.02,.001]}
    with pytest.raises(ValueError,match='Bornes incohérentes'): calculate(c)


def test_physics_never_borrows_pp_accuracy_and_survives_all_outputs():
    result=calculate(exposure='outdoor')
    assert result['manifest']['assumptions']['validation']=={}
    assert result['manifest']['precision']['reference_precision_pct'] is None
    assert result['manifest']['reliability']['code']=='parameterised_research_model'
    assert result['manifest']['reliability_95']['qualified'] is False
    assert result['manifest']['source']['sources']==[]
    json.dumps(result,allow_nan=False)
    assert curve(result).data
    assert sampled_curve_rows(result)
    assert result_workbook(result).startswith(b'PK')
    assert markdown_report(result)
    assert len(PdfReader(io.BytesIO(result_pdf(result))).pages)==4
    snapshot=freeze_prediction(result,'Hypothèse avant essais')
    assert snapshot['model_manifest']['family_physics']['parameters']['thermal_rate_day']==.01
    result['manifest']['family_physics']['parameters']['thermal_rate_day']=9
    assert snapshot['model_manifest']['family_physics']['parameters']['thermal_rate_day']==.01
