import run_job_utility


def test_biomarkers(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job/biomarkers.csv",
                                    config="test_config.yaml",
                                    cwd="run_job",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job/biomarkers.csv")

    assert gold == lead


def test_discarded(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job/discarded.csv",
                                    config="test_config.yaml",
                                    cwd="run_job",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job/discarded.csv")

    assert gold == lead


def test_discarded_because_of_nans(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job/discarded_because_of_nans.csv",
                                    config="test_config.yaml",
                                    cwd="run_job",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job/discarded_because_of_nans.csv")

    assert gold == lead


def test_success(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job/success.csv",
                                    config="test_config.yaml",
                                    cwd="run_job",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job/success.csv")

    assert gold == lead


def test_simulation_manifest(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job/simulation_manifest.csv",
                                    config="test_config.yaml",
                                    cwd="run_job",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job/simulation_manifest.csv")

    assert gold == lead


def test_run_cells_cmd(job_session_fixture):
    cmds_gold = run_job_utility.get_gold_list(files=[f"run_job/cell_{i + 1}/cmd.txt" for i in range(0, 5)])

    cmds_lead = [run_job_utility.get_lead(file=f"run_job/cell_{i + 1}/cmd.txt",
                                          config="test_config.yaml",
                                          cwd="run_job",
                                          patch_count=1,
                                          patch_idx=0) for i in range(0, 5)]

    assert cmds_gold == cmds_lead


def test_run_cells_stderr(job_session_fixture):
    stderr_gold = run_job_utility.get_gold_list(files=[f"run_job/cell_{i + 1}/stderr.txt" for i in range(0, 5)])

    stderr_lead = [run_job_utility.get_lead(file=f"run_job/cell_{i + 1}/stderr.txt",
                                            config="test_config.yaml",
                                            cwd="run_job",
                                            patch_count=1,
                                            patch_idx=0) for i in range(0, 5)]

    assert stderr_gold == stderr_lead


def test_used_all_generated_params(
        job_session_fixture):  # Checks only if all the elements were used. Does not care about order
    manifest = run_job_utility.get_lead(file="run_job/simulation_manifest.csv",
                                        config="test_config.yaml",
                                        cwd="run_job",
                                        patch_count=1,
                                        patch_idx=0)
    cmds_lead = [run_job_utility.get_lead(file=f"run_job/cell_{i + 1}/cmd.txt",
                                          config="test_config.yaml",
                                          cwd="run_job",
                                          patch_count=1,
                                          patch_idx=0) for i in range(0, 5)]

    gen_params = run_job_utility.get_params_from_text(manifest)
    used_params = run_job_utility.get_params_from_text('\n'.join(cmds_lead))

    assert sorted(gen_params) == sorted(used_params)


def test_correct_order(job_session_fixture):  # Same as test_used_all_generated_params except without sorting
    manifest = run_job_utility.get_lead(file="run_job/simulation_manifest.csv",
                                        config="test_config.yaml",
                                        cwd="run_job",
                                        patch_count=1,
                                        patch_idx=0)
    cmds_lead = [run_job_utility.get_lead(file=f"run_job/cell_{i + 1}/cmd.txt",
                                          config="test_config.yaml",
                                          cwd="run_job",
                                          patch_count=1,
                                          patch_idx=0) for i in range(0, 5)]

    gen_params = run_job_utility.get_params_from_text(manifest)
    used_params = run_job_utility.get_params_from_text('\n'.join(cmds_lead))

    assert gen_params == used_params


def test_unique_params(job_session_fixture):
    manifest = run_job_utility.get_lead(file="run_job/simulation_manifest.csv",
                                        config="test_config.yaml",
                                        cwd="run_job",
                                        patch_count=1,
                                        patch_idx=0)

    gen_params = run_job_utility.get_params_from_text(manifest)

    assert len(gen_params) == len(set(gen_params))


def test_naming(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_patch-1-5/biomarkers.csv-1-5",
                                    config="test_config.yaml",
                                    cwd="run_job_patch",
                                    patch_count=5,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_patch-1-5/biomarkers.csv-1-5")
    assert lead == gold


def test_patch(job_session_fixture):
    # Collect commands from run without patches as our gold
    gold = [run_job_utility.get_lead(file=f"run_job/cell_{i + 1}/cmd.txt",
                                     config="test_config.yaml",
                                     cwd="run_job",
                                     patch_count=1,
                                     patch_idx=0) for i in range(0, 5)]
    # Collect commands from run with patches as our lead
    lead = [run_job_utility.get_lead(file=f"run_job_patch-{i + 1}-5/cell_{i + 1}/cmd.txt",
                                     config="test_config.yaml",
                                     cwd="run_job_patch",
                                     patch_count=5,
                                     patch_idx=i) for i in range(0, 5)]

    assert gold == lead
