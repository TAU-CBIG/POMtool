#!/usr/bin/env python3

import argparse
import yaml

class Model:
    def __init__(self, full_args) -> None:
        self.exec = None
        self.cwd = None
        self.pars = []
        for args in full_args:
            if 'exec' in args:
                if self.exec != None:
                    raise ValueError('Multiple model exec defined.')
                self.exec = args['exec']
            if 'cwd' in args:
                if self.cwd != None:
                    raise ValueError('Multiple model cwd defined')
                self.cwd = args['cwd']
            if 'par' in args:
                self.pars.append(args['par'])

    def __str__(self) -> str:
        return f"{self.cwd} | {self.exec} {' '.join(self.pars)}" 


class Models:
    def __init__(self, args) -> None:
        self.models = {}
        location = 0
        while location < len(args):
            tmp_args = [args[location]]
            id = args[location]['id']
            location += 1
            while location < len(args) and 'par' in args[location]:
                tmp_args.append(args[location])
                location += 1
            self.models[id] = Model(tmp_args)

    def __str__(self) -> str:
        ret_val = []
        for id, model in self.models.items():
            ret_val.append(f'{id}: {model}')
        return '\n'.join(ret_val)

class Experiment:
    def __init__(self, args) -> None:
        self.name = args['name']
        self.id = args['id']
        self.model = args['model']
        self.parametrization = args['parametrization']
        self.cells = args['cells']
        self.parametrization_length = args['parametrization_length']
        self.manifest = args['manifest']

    def __str__(self) -> str:
        return self.id


class BiomarkerSet:
    def __init__(self, args) -> None:
        self.id = args[0]['id']
        self.window = args[0]['window']
        self.target = args[0]['target']
        self.biomarkers = []
        for i in range(1,len(args)):
            self.biomarkers.append(args[i]['biomarker'])

    def __str__(self) -> str:
        return f'{self.id} | {self.window} | {self.target} | {",".join(self.biomarkers)}'


class Biomarkers:
    def __init__(self, args) -> None:
        self.biomarkers = {}
        location = 0
        while location < len(args):
            tmp_args = [args[location]]
            id = args[location]['id']
            location += 1
            while location < len(args) and 'biomarker' in args[location]:
                tmp_args.append(args[location])
                location += 1
            self.biomarkers[id] = BiomarkerSet(tmp_args)

    def __str__(self) -> str:
        ret_val = []
        for id, biomarker_set in self.biomarkers.items():
            ret_val.append(f'{id}: {biomarker_set}')
        return '\n'.join(ret_val)

class Calibration:
    def __init__(self, args) -> None:
        self.calibrations = args

    def __str__(self) -> str:
        return str(self.calibrations)

def run():
    parser = argparse.ArgumentParser(
            prog='Foobar',
            description='Generate population of models based on the config file given',
            epilog='See example'
            )
    parser.add_argument('--config', required=True, help='Config file to do the thing')
    parser.add_argument('--dry', action='store_true',)
    args = parser.parse_args()
    if args.dry:
        print('Dry run')
    if args.config:
        print('Using config ', args.config)
    with open(args.config, 'r') as f:
        content = yaml.safe_load(f)
        models = Models(content['model'])
        experiment = Experiment(content['experiment'][0])
        biomarkers = Biomarkers(content['biomarkers'])
        calibration = Calibration(content['calibration'])
        print('\n--models--')
        print(models)
        print('\n--experiment--')
        print(experiment)
        print('\n--biomarkers--')
        print(biomarkers)
        print('\n--calibration--')
        print(calibration)

if __name__ == '__main__':
    run()
