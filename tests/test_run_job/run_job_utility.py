import sys

sys.path.append('../..')
import src.main
import pathlib
import yaml
import os
import shutil
import re

skip = False
GOLD = "gold"
LEAD = "lead"
EXPERIMENT = "experiment"
CWD = "cwd"
NAME = "name"
CELLS = "cells"

ALREADY_RAN = []


def get_lead(config, file, patch_count=1, patch_idx=0) -> str:
    dir_lead = "../data/lead/"
    file_lead = dir_lead + file
    file_lead = pathlib.Path(file_lead)
    original_path = os.getcwd()

    file_lead.parent.mkdir(exist_ok=True, parents=True)

    argument = [f"--config={config}", f"--force", f"--patch_count={patch_count}", f"--patch_idx={patch_idx}",
                "--silent"]

    if not skip and argument not in ALREADY_RAN:
        #this is because of a bug: cwd should always be where --config=foo.yaml is -> fix this at some point
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


def get_config_content(config, section, key):
    with open(config, 'r') as f:
        content = yaml.safe_load(f)
    info = content[section][0][key]
    return info


def get_subdir_cell_data(config, file, folder_type, patch_count=1,
                         patch_idx=0):
    num_of_cells = get_config_content(config=config, section=EXPERIMENT, key=CELLS)
    subdir_name = get_config_content(config=config, section=EXPERIMENT, key=NAME)[:-1]  # Get the place of number out
    cwd = get_config_content(config=config, section=EXPERIMENT, key=CWD)
    subdir_data = {}
    failed_files = []
    for cell in range(num_of_cells):
        cell += 1
        file_path = f"{cwd}/{subdir_name}{cell}/{file}"
        if folder_type == LEAD:
            type_file = get_lead(config=config, file=file_path, patch_count=patch_count, patch_idx=patch_idx)
        elif folder_type == GOLD:
            try:
                type_file = get_gold(file=file_path)
            except FileNotFoundError as e:
                failed_files.append(file_path)
                type_file = None
        else:
            raise NotImplementedError(f"Not implemented type: {folder_type}")

        subdir_data[cell] = type_file
    if failed_files:
        raise FileNotFoundError(f"{len(failed_files)} gold files failed to load: `{'´, ´'.join(failed_files)}`")
    return subdir_data


def dict_to_text(dictionary):
    all_text = ""
    for cmd in dictionary.values():
        all_text = all_text + " " + cmd

    return all_text


def get_params_from_text(text) -> list:
    # Matches to "number.number"
    params = re.findall("[0-9]{1,}\\.[0-9]{1,}", text)
    return params
