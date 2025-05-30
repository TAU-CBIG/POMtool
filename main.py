#!/usr/bin/env python3

import argparse
import pathlib
import shutil
import yaml
#import matplotlib.pyplot as plt # temp debug
import merge
import experiment as exp
import model as mod
import biomarker as bm
import calibration as cal
import sys

def run_merge(arg_list):
    parser = argparse.ArgumentParser(
            prog='merge',
            description='Merge already run populations into same format as it were run in single pass. Use same config file, as when generating. Will collect all the files and results.',
            epilog='See example_config.yaml for the config'
            )
    parser.add_argument('--patch_count', help='Define how many patches were used', required=True, metavar="N", type=int)
    parser.add_argument('--config', required=True, help='Config file to do the thing')
    parser.add_argument('--files-mode', choices= ['copy', 'move'], default='copy', help='Define whether files should be copied or moved.')
    parser.add_argument('--dry', action='store_true',help='Run without actually doing the experiment.')
    # parser.add_argument('--silent', action='store_true',help='Silent control flow printing')
    parser.add_argument('--skip-experiment', action='store_true',help='Skip experiment merging')
    parser.add_argument('--only-experiment', action='store_true',help='Only merge experiment')
    parser.add_argument('--skip-biomarkers', action='store_true',help='Skip biomarkers merge')
    parser.add_argument('--only-biomarkers', action='store_true',help='Only merge biomarker file')
    parser.add_argument('--skip-calibration', action='store_true',help='Skip calibration merging')
    parser.add_argument('--only-calibration', action='store_true',help='Only merge calibration')
    parser.add_argument('--force', action='store_true', help='Override existing files during the experiment')

    args = parser.parse_args(arg_list)

    if args.only_experiment:
        args.skip_biomarkers = True
        args.skip_calibration = True
    if args.only_biomarkers:
        args.skip_experiment = True
        args.skip_calibration = True
    if args.only_calibration:
        args.skip_experiment = True
        args.skip_biomarkers = True

    with open(args.config, 'r') as f:
        content = yaml.safe_load(f)

    merger = merge.Merge(content, args.patch_count, args.force, args.dry)
    if not args.skip_experiment:
        merger.merge_experiments()
    if not args.skip_biomarkers:
        merger.merge_biomarkers()
    if not args.skip_calibration:
        merger.merge_calibration()


def run_job(arg_list):
    parser = argparse.ArgumentParser(
            prog='run',
            description='Generate population of models based on the config file given',
            epilog='See example_config.yaml for the config'
            )
    parser.add_argument('--config', required=True, help='Config file to do the thing')
    parser.add_argument('--dry', action='store_true',help='Run without actually doing the experiment.')
    parser.add_argument('--silent', action='store_true',help='Silent control flow printing')
    parser.add_argument('--patch_count', help='Define how many patches are going to be used', default=1, metavar="N", type=int)
    parser.add_argument('--patch_idx', help='Define what patch is going to be used for this specific run, range [0,patch_count)', default=0, metavar="IDX", type=int)
    parser.add_argument('--skip-experiment', action='store_true',help='Skip experiment, it is assumed you already have run experiment')
    parser.add_argument('--only-experiment', action='store_true',help='Only run experiment')
    parser.add_argument('--skip-biomarkers', action='store_true',help='Skip biomarkers, following steps might expect biomarkers to exist')
    parser.add_argument('--only-biomarkers', action='store_true',help='Only run biomarkers, you need to have experiment already run and in correct format')
    parser.add_argument('--skip-calibration', action='store_true',help='Skip calibration')
    parser.add_argument('--only-calibration', action='store_true',help='Only run calibration, assumes you have run previous steps already and have the data')
    parser.add_argument('--force', action='store_true', help='Override existing files during the experiment')
    args = parser.parse_args(arg_list)
    def noprint(*values: object,):
        pass

    myprint = noprint if args.silent else print
    if args.config:
        myprint(f'Using config `{args.config}`')
    with open(args.config, 'r') as f:
        content = yaml.safe_load(f)
    if args.only_experiment:
        args.skip_biomarkers = True
        args.skip_calibration = True
    if args.only_biomarkers:
        args.skip_experiment = True
        args.skip_calibration = True
    if args.only_calibration:
        args.skip_experiment = True
        args.skip_biomarkers = True
    models = mod.Models(content['model'])
    experiment = exp.Experiment(content['experiment'][0], args.patch_idx, args.patch_count)
    if not args.skip_experiment:
        myprint('Start experiments')
        if not args.dry:
            if pathlib.Path(experiment.cwd).exists():
                if args.force:
                    print("REMOVE:", experiment.cwd)
                    shutil.rmtree(experiment.cwd)
                else:
                    raise FileExistsError(f'Target directory exists `{experiment.cwd}`')

            experiment.run(models)
        else:
            experiment.dry(models)
        myprint('End experiments')
    if not args.skip_biomarkers:
        myprint('Start biomarkers')
        biomarkers = bm.Biomarkers(content['biomarkers'], args.patch_idx, args.patch_count)
        if args.skip_experiment:
            experiment.empty_run(models)
        if not args.dry:
            biomarkers.run(experiment)
        else:
            biomarkers.dry(experiment)
        myprint('End biomarkers')
    if not args.skip_calibration:
        myprint('Start calibration')
        if not args.dry:
            calibration = cal.Calibration(content['calibration'], experiment, args.patch_idx, args.patch_count)
            calibration.run()
        else:
            print(content['calibration'])
        myprint('End calibration')


def run():
    parser = argparse.ArgumentParser(
            prog='main',
            description='Generate population of models based on the config file given. Either use run to generate population, or merge to merge population run done in patches.',
            epilog='See example_config.yaml for the config'
            )
    RUN = 'run'
    MERGE = 'merge'
    parser.add_argument('mode', choices=[RUN, MERGE], help=f"Used mode, either `{RUN}` or `{MERGE}`, or by default use `run`")
    arg_list = sys.argv[1:]
    if len(sys.argv) < 2:
        parser.print_help()
        return
    elif sys.argv[1][0] == '-':
        mode = 'run'
    else:
        args = parser.parse_args([sys.argv[1]])
        mode = args.mode
        arg_list = arg_list[1:] # first argument handled
    if mode == RUN:
        run_job(arg_list)
    elif mode == MERGE:
        run_merge(arg_list)
    else:
        parser.print_help()


if __name__ == '__main__':
    run()
