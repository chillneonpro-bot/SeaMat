from seamat import material_db
from seamat.modeling import estimate_from_datasheet, standard_profile
from seamat.reliability import GATE_VERSION, assess_result, material_coverage


def estimate(material_id, days, temperature=23, exposure='outdoor', medium=None):
    material=material_db.material(material_id)
    profile=standard_profile(material)
    return estimate_from_datasheet(
        material,profile['suggested_modulus_mpa'],temperature,50,2,days/365.25,80,
        exposure,material_db.model_evidence_rows(material_id,exposure),medium,
    )


def test_documentary_curve_is_never_presented_as_reliable():
    material=material_db.material('PEEK'); profile=standard_profile(material)
    result=estimate_from_datasheet(material,profile['suggested_modulus_mpa'],23,50,2,2,80,'indoor',[])
    reliability=result['manifest']['reliability']
    assert reliability['gate_version']==GATE_VERSION
    assert reliability['code']=='documentary_only'
    assert reliability['usable_for_screening'] is False
    assert reliability['qualified_external'] is False


def test_pp_is_internal_only_inside_its_published_window():
    inside=estimate('PP',120)
    outside=estimate('PP',365)
    assert inside['manifest']['reliability']['code']=='internally_supported'
    assert inside['manifest']['reliability']['usable_for_screening'] is True
    assert inside['manifest']['reliability']['qualified_external'] is False
    claim=inside['manifest']['reliability_95']
    assert claim['target_coverage_pct']==95
    assert claim['confidence_level_pct']==95
    assert claim['qualified'] is False
    assert claim['independent_groups']==4
    assert claim['one_sided_lower_bound_pct']<95
    assert claim['additional_groups_best_case']==55
    assert outside['manifest']['reliability']['code']=='extrapolation_unqualified'
    assert outside['manifest']['reliability']['usable_for_screening'] is False


def test_iir_exact_profile_and_temperature_transfer_have_distinct_decisions():
    exact=estimate('IIR',1,100,'immersion','milform64')
    transfer=estimate('IIR',1,90,'immersion','milform64')
    assert exact['manifest']['reliability']['code']=='published_exact_unvalidated'
    assert exact['manifest']['reliability']['usable_for_screening'] is True
    assert transfer['manifest']['reliability']['code']=='validation_failed'
    assert transfer['manifest']['reliability']['usable_for_screening'] is False


def test_every_catalogue_material_receives_the_same_coverage_contract():
    reports=[material_coverage(item,material_db.model_evidence_rows(item['id']))
             for item in material_db.catalog()]
    assert len(reports)==75
    assert all(set(report['missing'])=={'rows','experiments','sources'} for report in reports)
    by_id={report['material_id']:report for report in reports}
    assert by_id['PP']['coverage_code']=='benchmark_ready'
    assert by_id['IIR']['coverage_code']=='evidence_limited'
    assert by_id['FLAX_EPOXY']['coverage_code']=='documentary_only'
    assert sum(report['can_claim_external_reliability'] for report in reports)==0


def test_95_95_claim_requires_59_fully_covered_independent_groups():
    def result(groups):
        return {'manifest':{'model':'datasheet-screening-v6-seamat-engine','assumptions':{
            'extrapolation_multiple':1,'profile_method':'experiment_transfer',
            'independent_sources':2,'documentary_match':{'score':90},
            'validation':{'test_predictions':groups,'mape_pct':3,'max_ape_pct':5,
                          'empirical_point_coverage_pct':100,
                          'independent_validation_groups':groups,
                          'covered_validation_groups':groups}}}}
    before=assess_result(result(58))
    qualified=assess_result(result(59))
    assert before['reliability_95']['qualified'] is False
    assert before['code']=='internally_supported'
    assert qualified['reliability_95']['qualified'] is True
    assert qualified['reliability_95']['one_sided_lower_bound_pct']>=95
    assert qualified['code']=='externally_supported'
