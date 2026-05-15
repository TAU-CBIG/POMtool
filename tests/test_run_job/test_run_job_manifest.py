import run_job_utility

def parameters(idx: int):
    val = ['straw', 'blue', 'rasp', 'cran', 'lingon']
    return val[idx]


def test_manifest_biomarkers(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_manifest/biomarkers.csv",
                                    config="test_config_manifest.yaml",
                                    cwd="run_job_manifest",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_manifest/biomarkers.csv")

    assert gold == lead


def test_manifest_discarded(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_manifest/discarded.csv",
                                    config="test_config_manifest.yaml",
                                    cwd="run_job_manifest",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_manifest/discarded.csv")

    assert gold == lead


def test_manifest_discarded_because_of_nans(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_manifest/discarded_because_of_nans.csv",
                                    config="test_config_manifest.yaml",
                                    cwd="run_job_manifest",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_manifest/discarded_because_of_nans.csv")

    assert gold == lead


def test_manifest_success(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_manifest/success.csv",
                                    config="test_config_manifest.yaml",
                                    cwd="run_job_manifest",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_manifest/success.csv")

    assert gold == lead


def test_manifest_simulation_manifest(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_manifest/simulation_manifest.csv",
                                    config="test_config_manifest.yaml",
                                    cwd="run_job_manifest",
                                    patch_count=1,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_manifest/simulation_manifest.csv")

    assert gold == lead


def test_manifest_run_cells_cmd(job_session_fixture):
    names = []
    cmds_gold = run_job_utility.get_gold_list(files=[f"run_job_manifest/{parameters(i)}/cmd.txt" for i in range(0, 5)])

    cmds_lead = [run_job_utility.get_lead(file=f"run_job_manifest/{parameters(i)}/cmd.txt",
                                          config="test_config_manifest.yaml",
                                          cwd="run_job_manifest",
                                          patch_count=1,
                                          patch_idx=0) for i in range(0, 5)]

    assert cmds_gold == cmds_lead


def test_manifest_run_cells_stderr(job_session_fixture):
    stderr_gold = run_job_utility.get_gold_list(files=[f"run_job_manifest/{parameters(i)}/stderr.txt" for i in range(0, 5)])

    stderr_lead = [run_job_utility.get_lead(file=f"run_job_manifest/{parameters(i)}/stderr.txt",
                                            config="test_config_manifest.yaml",
                                            cwd="run_job_manifest",
                                            patch_count=1,
                                            patch_idx=0) for i in range(0, 5)]

    assert stderr_gold == stderr_lead


def test_manifest_used_all_generated_params(
        job_session_fixture):  # Checks only if all the elements were used. Does not care about order
    manifest = run_job_utility.get_lead(file="run_job_manifest/simulation_manifest.csv",
                                        config="test_config_manifest.yaml",
                                        cwd="run_job_manifest",
                                        patch_count=1,
                                        patch_idx=0)
    cmds_lead = [run_job_utility.get_lead(file=f"run_job_manifest/{parameters(i)}/cmd.txt",
                                          config="test_config_manifest.yaml",
                                          cwd="run_job_manifest",
                                          patch_count=1,
                                          patch_idx=0) for i in range(0, 5)]

    gen_params = run_job_utility.get_params_from_text(manifest)
    used_params = run_job_utility.get_params_from_text('\n'.join(cmds_lead))

    assert sorted(gen_params) == sorted(used_params)


def test_manifest_correct_order(job_session_fixture):  # Same as test_used_all_generated_params except without sorting
    manifest = run_job_utility.get_lead(file="run_job_manifest/simulation_manifest.csv",
                                        config="test_config_manifest.yaml",
                                        cwd="run_job_manifest",
                                        patch_count=1,
                                        patch_idx=0)
    cmds_lead = [run_job_utility.get_lead(file=f"run_job_manifest/{parameters(i)}/cmd.txt",
                                          config="test_config_manifest.yaml",
                                          cwd="run_job_manifest",
                                          patch_count=1,
                                          patch_idx=0) for i in range(0, 5)]

    gen_params = run_job_utility.get_params_from_text(manifest)
    used_params = run_job_utility.get_params_from_text('\n'.join(cmds_lead))

    assert gen_params == used_params


def test_manifest_unique_params(job_session_fixture):
    manifest = run_job_utility.get_lead(file="run_job_manifest/simulation_manifest.csv",
                                        config="test_config_manifest.yaml",
                                        cwd="run_job_manifest",
                                        patch_count=1,
                                        patch_idx=0)

    gen_params = run_job_utility.get_params_from_text(manifest)


    assert len(gen_params) == len(set(gen_params))


def test_manifest_naming(job_session_fixture):
    lead = run_job_utility.get_lead(file="run_job_manifest_patch-1-2/biomarkers.csv-1-2",
                                    config="test_config_manifest.yaml",
                                    cwd="run_job_manifest_patch",
                                    patch_count=2,
                                    patch_idx=0)
    gold = run_job_utility.get_gold(file="run_job_manifest_patch-1-2/biomarkers.csv-1-2")
    assert lead == gold


def test_manifest_patch(job_session_fixture):
    # Collect commands from run without patches as our gold
    gold = [run_job_utility.get_lead(file=f"run_job_manifest/{parameters(i)}/cmd.txt",
                                     config="test_config_manifest.yaml",
                                     cwd="run_job_manifest",
                                     patch_count=1,
                                     patch_idx=0) for i in range(0, 5)]
    # Collect commands from run with patches as our lead
    lead = [run_job_utility.get_lead(file=f"run_job_manifest_patch-{i // 3 + 1}-2/{parameters(i)}/cmd.txt",
                                     config="test_config_manifest.yaml",
                                     cwd="run_job_manifest_patch",
                                     patch_count=2,
                                     patch_idx=i // 3) for i in range(0, 5)]

    assert gold == lead


def test_manifest_merge(job_session_fixture):
    gold = run_job_utility.get_lead(file="run_job_manifest/simulation_manifest.csv",
                                    config="test_config_manifest.yaml",
                                    cwd="run_job_manifest",
                                    patch_count=1,
                                    patch_idx=0)

    ensure = [run_job_utility.get_lead(file=f"run_job_manifest_patch-{i // 3 + 1}-2/simulation_manifest.csv-{i // 3 + 1}-2",
                                       config="test_config_manifest.yaml",
                                       cwd="run_job_manifest_patch",
                                       patch_count=2,
                                       patch_idx=i // 3) for i in range(0, 5)]

    lead = run_job_utility.get_lead_merge(file="run_job_manifest/simulation_manifest.csv",
                                          config="test_config_manifest.yaml",
                                          cwd="run_job_manifest_patch",
                                          patch_count=2)
    assert gold == lead
