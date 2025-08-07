import sys

sys.path.append('../..')
import src.main
import pathlib
import os
import shutil

ALREADY_RAN = []


def get_lead(config, file, patch_count=1, patch_idx=0) -> str:
    dir_lead = "../data/lead/"
    file_lead = dir_lead + file
    file_lead = pathlib.Path(file_lead)
    original_path = os.getcwd()

    file_lead.parent.mkdir(exist_ok=True, parents=True)

    argument = [f"--config={config}", f"--force", f"--patch_count={patch_count}", f"--patch_idx={patch_idx}",
                "--silent"]

    if argument not in ALREADY_RAN:
        # this is because of a bug: cwd should always be where --config=foo.yaml is -> fix this at some point
        shutil.copytree(original_path, dir_lead, dirs_exist_ok=True)
        try:
            os.chdir(dir_lead)
            src.main.run_job(argument)
        except:
            pass
        os.chdir(original_path)
        ALREADY_RAN.append(argument)
    data = file_lead.read_text()
    return data


def get_gold(file) -> str:
    gold_dir = pathlib.Path("../data/gold/")
    file_gold = gold_dir / file

    if not file_gold.exists():
        raise FileNotFoundError(f"Gold file '{file}' not found from '{gold_dir.resolve()}'")

    data = file_gold.read_text()
    return data
