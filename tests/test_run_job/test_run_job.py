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


def test_success():
    lead = run_job_utility.get_lead(file="run_job/success.csv",
                                    config="test_config_run_job.yaml",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job/success.csv")

    assert gold == lead


def test_simulation_manifest():
    lead = run_job_utility.get_lead(file="run_job/simulation_manifest.csv",
                                    config="test_config_run_job.yaml",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job/simulation_manifest.csv")

    assert gold == lead


def test_run_cells_cmd():
    cmds_gold = run_job_utility.get_subdir_cell_data(config="test_config_run_job.yaml",
                                                     folder_type=run_job_utility.GOLD,
                                                     file="cmd.txt",
                                                     patch_count=1,
                                                     patch_idx=0)
    cmds_lead = run_job_utility.get_subdir_cell_data(config="test_config_run_job.yaml",
                                                     folder_type=run_job_utility.LEAD,
                                                     file="cmd.txt",
                                                     patch_count=1,
                                                     patch_idx=0)

    assert cmds_gold == cmds_lead


def test_run_cells_stderr():
    stderr_gold = run_job_utility.get_subdir_cell_data(config="test_config_run_job.yaml",
                                                       folder_type=run_job_utility.GOLD,
                                                       file="stderr.txt",
                                                       patch_count=1,
                                                       patch_idx=0)
    stderr_lead = run_job_utility.get_subdir_cell_data(config="test_config_run_job.yaml",
                                                       folder_type=run_job_utility.LEAD,
                                                       file="stderr.txt",
                                                       patch_count=1,
                                                       patch_idx=0)

    assert stderr_gold == stderr_lead
