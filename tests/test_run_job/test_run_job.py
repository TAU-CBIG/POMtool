import run_job_utility


def test_biomarkers():
    lead = run_job_utility.get_lead(file="run_job/biomarkers.csv",
                                    config="test_config_run_job.yaml",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job/biomarkers.csv")

    assert gold == lead


def test_discarded():
    lead = run_job_utility.get_lead(file="run_job/discarded.csv",
                                    config="test_config_run_job.yaml",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job/discarded.csv")

    assert gold == lead


def test_discarded_because_of_nans():
    lead = run_job_utility.get_lead(file="run_job/discarded_because_of_nans.csv",
                                    config="test_config_run_job.yaml",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job/discarded_because_of_nans.csv")

    assert gold == lead
