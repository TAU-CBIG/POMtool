import sys

sys.path.append('../..')
import src.main
import pathlib
import yaml
import os
import shutil
import re
import datetime

skip = False
GOLD = "gold"
LEAD = "lead"
EXPERIMENT = "experiment"
CWD = "cwd"
NAME = "name"
CELLS = "cells"

ALREADY_RAN = []


def config_name(config: pathlib.Path, path) -> str:
    return config.stem + "_" + path + config.suffix


def copy_config(config: pathlib.Path, path) -> None:
    content = ""
    with open(config, 'r') as f:
        content = f.read()
    content = content.replace('CWD_REPLACE', path)
    with open(config_name(config, path), 'w') as f:
        f.write(content)


def get_lead(config, cwd, file, patch_count=1, patch_idx=0) -> str:
    dir_lead = "../data/lead/"
    file_lead = dir_lead + file
    file_lead = pathlib.Path(file_lead)
    original_path = os.getcwd()
    config = pathlib.Path(config)

    file_lead.parent.mkdir(exist_ok=True, parents=True)
    config_cwd = config_name(config, cwd)
    argument = [f"--config={config_cwd}", f"--force", f"--patch_count={patch_count}", f"--patch_idx={patch_idx}",
                "--silent"]

    if not skip and argument not in ALREADY_RAN:
        # this is because of a bug: cwd should always be where --config=foo.yaml is -> fix this at some point
        shutil.copytree(original_path, dir_lead, dirs_exist_ok=True)
        try:
            os.chdir(dir_lead)
            copy_config(config, cwd)
            src.main.run_job(argument)
            os.chdir(original_path)
        except Exception as e:
            os.chdir(original_path)
            raise e
        ALREADY_RAN.append(argument)
    data = file_lead.read_text()
    return data


gold_files = []


def get_gold_list(files):
    golds = []
    for f in files:
        try:
            golds.append(get_gold(f))
        except FileNotFoundError as e:
            pass
    return golds


def get_gold(file) -> str:
    gold_files.append(file)
    gold_dir = pathlib.Path("../data/gold/")
    file_gold = gold_dir / file

    if not file_gold.exists():
        raise FileNotFoundError(f"Gold file '{file}' not found from '{gold_dir.resolve()}'")

    data = file_gold.read_text()
    return data


def get_config_content(config, section, key):
    with open(config, 'r') as f:
        content = yaml.safe_load(f)
    info = content[section][0][key]
    return info


def get_params_from_text(text) -> list:
    # Matches to "number.number"
    params = re.findall("[0-9]{1,}\\.[0-9]{1,}", text)
    return params


def log_gold(file: pathlib.Path, function: str):
    log_file = "../data/gold/logs.txt"
    with open(log_file, 'a') as f:
        f.write(f"{function} {file} : {datetime.datetime.now()}\n")


def diff_of_files(file1, file2) -> bool:
    try:
        with open(file1, 'r') as f1:
            with open(file2, 'r') as f2:
                content1 = f1.read()
                content2 = f2.read()
                return content1 == content2
    except:
        return False


def make_gold_file(file: str):
    file_lead = pathlib.Path("../data/lead/" + file)
    file_gold = pathlib.Path("../data/gold/" + file)
    file_gold.parent.mkdir(exist_ok=True, parents=True)

    if file_gold.exists():
        if diff_of_files(file_gold, file_lead):
            return  # Nothing to do

        log_gold(file_gold, function="Change")
        os.remove(file_gold)
    else:
        log_gold(file_gold, function="Add")
    shutil.copy(file_lead, file_gold)


def delete_gold_file(file: str):
    file_gold = pathlib.Path("../data/gold/" + file)
    if file_gold.exists():
        os.remove(file_gold)
        log_gold(file_gold, function="Del")
