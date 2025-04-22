#!/usr/bin/env python3

import argparse
import yaml
import matplotlib.pyplot as plt # temp debug
import experiment as exp
import model as mod
import biomarker as bm
import calibration as cal

def run():
    parser = argparse.ArgumentParser(
            prog='Foobar',
            description='Generate population of models based on the config file given',
            epilog='See example'
            )
    parser.add_argument('--config', required=True, help='Config file to do the thing')
    parser.add_argument('--dry', action='store_true',)
    args = parser.parse_args()
    if args.config:
        print(f'Using config `{args.config}`')
    with open(args.config, 'r') as f:
        content = yaml.safe_load(f)
    models = mod.Models(content['model'])
    experiment = exp.Experiment(content['experiment'][0])
    biomarkers = bm.Biomarkers(content['biomarkers'])
    calibration = cal.Calibration(content['calibration'])

    if args.dry:
        # Run all experiments
        experiment.dry(models)

        # Calculate biomarkers for each `target` instance
        biomarkers.dry(experiment)

        # Go through each calibration condition
        print(calibration)
    else:
        # Run all experiments
        # experiment.dry(models)

        # print("START biomarker")
        # Calculate biomarkers for each `target` instance
        # biomarkers.run(experiment)
        # print('biomarkers: ', biomarkers.biomarkers)

        calibration.run()

        # points = experiment.get_data(['time', 'Cai', 'Vm', 'iStim'], 0)
        # plt.plot(points['time'], points['Cai'])
        # plt.show()


if __name__ == '__main__':
    run()
