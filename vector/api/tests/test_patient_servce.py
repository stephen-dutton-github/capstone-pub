import pytest
from unittest.mock import MagicMock, patch
from api.services.patient_services import Patient, PatientServices, Admission



@pytest.fixture
def patient_services():
    service = PatientServices(file_locator=":memory:")
    service.execute_sql = MagicMock()
    return service


def test_get_admissions(patient_services):
    mock_admissions = [
                    {
                        "subject_id": 10001,"first_name": "John","family_name": "Doe","hadm_id": 50001,"admittime": "2024-02-12",
                        "anchor_age": 45,"seq_num": 1,"icd_code": "I10","icd_version": 10,"long_title": "Essential hypertension"
                    },
                    {
                        "subject_id": 10002,"first_name": "Jane","family_name": "Smith","hadm_id": 50002,"admittime": "2024-03-01",
                        "anchor_age": 38,"seq_num": 2,"icd_code": "J45","icd_version": 10,"long_title": "Asthma, unspecified"
                    }
    
                ]
    patient_services.execute_sql = MagicMock(return_value=mock_admissions)

    results = patient_services.get_admissions()

    assert len(results) == 2
    assert results[0].subject_id == 10001
    assert results[0].family_name == "Doe"
    assert results[0].long_title == "Essential hypertension"

    assert results[1].subject_id == 10002
    assert results[1].family_name == "Smith"
    assert results[1].icd_code == "J45"

    patient_services.execute_sql.assert_called_once()


def test_get_subjects(patient_services):
    expected_subjects = ["10001", "10002", "10003"]
    patient_services.execute_sql = MagicMock(return_value=(expected_subject_ids := ["10001", "10002", "10003"]))

    result = patient_services.get_subject_ids()

    assert result == expected_subject_ids
    patient_services.execute_sql.assert_called_once()


def test_search_by_subject_id(patient_services):
    subject_id = "1001"
    expected_results = [
        {"subject_id" : 1001,
         "first_name": "Olivia",
          "family_name": "Smith",
          "anchor_age" : 30,
          "anchor_year" :  2020}]
    patient_services.execute_sql = MagicMock(return_value=(expected_results := expected_results))
    result = patient_services.search_by_subject_id("1001")
    assert result[0].subject_id == expected_results[0].get("subject_id")
    patient_services.execute_sql.assert_called_once()
