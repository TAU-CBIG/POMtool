import run_job_utility
import pytest

def test_biomarkers_sensitivity(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_sensitivity/biomarkers.csv",
                                    config="test_config_sensitivity.yaml",
                                    cwd="run_job_sensitivity",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_sensitivity/biomarkers.csv")

    assert gold == lead


def test_discarded_sensitivity(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_sensitivity/discarded.csv",
                                    config="test_config_sensitivity.yaml",
                                    cwd="run_job_sensitivity",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_sensitivity/discarded.csv")

    assert gold == lead


def test_success_sensitivity(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_sensitivity/success.csv",
                                    config="test_config_sensitivity.yaml",
                                    cwd="run_job_sensitivity",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_sensitivity/success.csv")

    assert gold == lead


def test_simulation_manifest_sensitivity(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_sensitivity/simulation_manifest.csv",
                                    config="test_config_sensitivity.yaml",
                                    cwd="run_job_sensitivity",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_sensitivity/simulation_manifest.csv")

    assert gold == lead
