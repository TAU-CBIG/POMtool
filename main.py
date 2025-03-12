#!/usr/bin/env python3

import argparse
import yaml

class Model:
    def __init__(self, full_args) -> None:
        print(full_args)
        self.exec = None
        self.cwd = None
        self.param_key = ''
        self.pars = []
        for args in full_args:
            if 'exec' in args:
                if self.exec != None:
                    raise ValueError('Multiple model exec defined.')
                self.exec = args['exec']
            if 'param_key' in args:
                if self.param_key != '':
                    raise ValueError('Multiple model param_keys defined.')
                self.param_key = args['param_key']
            if 'cwd' in args:
                if self.cwd != None:
                    raise ValueError('Multiple model cwd defined')
                self.cwd = args['cwd']
            if 'par' in args:
                self.pars.append(args['par'])
        if self.param_key == '':
            self.param_key = '%#%'
        if self.exec == None:
            raise ValueError('exec not defined')
        if self.cwd == None:
            raise ValueError('cwd not defined')

    def __str__(self) -> str:
        return f"{self.cwd} | {self.exec} {' '.join(self.pars)}" 

    def dry(self, parameters) -> None:
        command = f'{self.exec} {" ".join(self.pars)}'
        # Replace parameters
        idx = 1
        for param in parameters:
            to_replace = self.param_key.replace('#', str(idx))
            if command.count(to_replace) == 0:
                print(f'Warning: Argument "{to_replace}" not found.')
            else:
                command = command.replace(to_replace, str(param))
            idx += 1
        print(f'dry run of\n    {command}')


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

    def dry(self, id, parameters) -> None:
        self.models[id].dry(parameters)


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
    if not args.dry:
        print('only dry implemented')
        return
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

        print('\n--script-running--')
        models.dry('my_matlab_model', [42,43])



if __name__ == '__main__':
    run()
