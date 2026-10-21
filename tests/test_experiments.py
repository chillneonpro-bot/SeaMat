from seamat.experiments import measurement_template_xlsx, parse_measurement_file, quality_report


def test_excel_template_roundtrip_and_quality_report():
    blob=measurement_template_xlsx()
    assert blob.startswith(b'PK')
    rows=parse_measurement_file(blob,'campagne.xlsx')
    report=quality_report(rows)
    assert len(rows)==8
    assert report['experiments']==2
    assert report['ready_for_review'] is True
    assert all(detail['has_t0'] for detail in report['details'])


def test_quality_report_flags_incomplete_experiment():
    rows=parse_measurement_file(measurement_template_xlsx(),'campagne.xlsx')[:2]
    report=quality_report(rows)
    assert report['ready_for_review'] is False
    assert report['blocking_count']>=1


def test_quality_report_handles_legacy_rows_without_new_conditions():
    rows=[{
        'experiment_id':'LEGACY','time_days':day,'modulus_MPa':value,
        'temperature_C':40,'material':'PP','protocol':'tensile','source':'Archive',
    } for day,value in ((0,1000),(10,950),(20,900))]
    report=quality_report(rows)
    assert report['ready_for_review'] is False
    assert report['conditions']['humidity_RH']==[]
    assert any('humidité relative' in flag['message'] for flag in report['flags'])


def test_template_can_be_fitted_without_mixed_temperature_error():
    from seamat.science import fit_measurements
    rows=parse_measurement_file(measurement_template_xlsx(),'campagne.xlsx')
    fit=fit_measurements(rows)
    assert fit['rate'] > 0
    assert fit['holdout_mae_MPa'] is not None


def test_excel_uses_measurements_even_if_instructions_are_active():
    import io
    from openpyxl import load_workbook
    workbook=load_workbook(io.BytesIO(measurement_template_xlsx()))
    workbook.active=1
    out=io.BytesIO(); workbook.save(out); workbook.close()
    assert len(parse_measurement_file(out.getvalue(),'campagne.xlsx')) == 8


def test_french_excel_csv_decimal_commas_and_header_whitespace():
    import csv
    import io
    from seamat.science import REQUIRED
    rows=parse_measurement_file(measurement_template_xlsx(),'campagne.xlsx')
    out=io.StringIO()
    writer=csv.writer(out,delimiter=';')
    writer.writerow([' '+key+' ' for key in REQUIRED])
    for row in rows:
        writer.writerow([str(row['raw'][key]).replace('.',',') if key in ('modulus','initial_modulus','thickness_mm') else row['raw'][key] for key in REQUIRED])
    parsed=parse_measurement_file(out.getvalue().encode('utf-8-sig'),'mesures.csv')
    assert len(parsed)==len(rows)
    assert parsed[1]['modulus_MPa']==rows[1]['modulus_MPa']
