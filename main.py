#!/usr/bin/env python3

import argparse
import yaml
import scipy.stats as sstats
import numpy as np

class Model:
    def __init__(self, full_args) -> None:
        print(full_args)
        self.exec = None
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
            if 'par' in args:
                self.pars.append(args['par'])
        if self.param_key == '':
            self.param_key = '%#%'
        if self.exec == None:
            raise ValueError('exec not defined')

    def __str__(self) -> str:
        return f"{self.exec} {' '.join(self.pars)}"

    def _create_command(self, parameters) -> str:
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
        return command

    def dry(self, cwd, parameters) -> None:
        command = self._create_command(parameters)
        print(f'dry run in {cwd} of\n    {command}')

    def run(self, cwd, parameters) -> None:
        command = self._create_command(parameters)
        # TODO: create directory for running
        # TODO: actually run the thing
        print(f'dry run in {cwd} of\n    {command}')

    def get_data(self, directory: str, names: list) -> np.ndarray:
        # TODO get the described with names from directory
        return  np.ndarray([])


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

    def model(self, id: str) -> Model:
        return self.models[id]


class Experiment:
    def __init__(self, args) -> None:
        self.name = args['name']
        self.id = args['id']
        self.model_id = args['model']
        self.cwd = args['cwd']
        self.parametrization = args['parametrization']
        self.cells = args['cells']
        self.parameter_count = args['parameter_count']
        self.manifest = args['manifest']

    def __str__(self) -> str:
        return self.id

    def _get_directory(self, idx) -> str:
        str_length = len(str(self.cells))
        return self.name.replace('#', str(idx+1).rjust(str_length, '0'))

    def _generate_parameters(self) -> np.ndarray:
        if self.parametrization == 'latin_hybercube':
            sampler = sstats.qmc.LatinHypercube(d=self.parameter_count, seed=0)
            return sampler.random(n=self.cells)
        else:
            raise ValueError(f'parametrization method "{self.parametrization}" not recognized')

    def _generate_manifest(self, parameters: np.ndarray) -> str:
        manifest = ''
        # run for each parameter
        for idx in range(0, self.cells):
            directory = self._get_directory(idx)
            manifest_line = [directory]
            for par in parameters[idx,:]:
                manifest_line.append(str(par))
            manifest += (', '.join(manifest_line)) + ";\n"
        return manifest

    def dry(self, models: Models) -> None:
        self.model: Model = models.model(self.model_id)
        # generate all parameters
        parameters = self._generate_parameters()
        manifest = self._generate_manifest(parameters)

        for idx in range(0, self.cells):
            directory = self._get_directory(idx)
            full_path = self.cwd + "/" + directory
            self.model.dry(full_path, parameters[idx,:])

        print(f'manifest: {self.manifest}:')
        print(manifest)

    def get_data(self, names: list, idx: int) -> np.ndarray:
        return self.model.get_data(self._get_directory(idx), names)

TIME = 'time'
VM = 'Vm'
CALSIUM = 'Ca'

class MDP:
    def __init__(self) -> None:
        pass

    def required_data(self) -> list:
        return [TIME, VM]

class APD90:
    def __init__(self) -> None:
        pass

    def required_data(self) -> list:
        return [TIME, VM]

class APD60:
    def __init__(self) -> None:
        pass

    def required_data(self) -> list:
        return [TIME, VM]


class Biomarkers:
    def __init__(self, args) -> None:
        self.id = args[0]['id']
        self.window = args[0]['window']
        self.target = args[0]['target']
        self.file = args[0]['file']
        self.biomarkers = []
        for i in range(1,len(args)):
            bio = args[i]['biomarker']
            if bio == "MDP":
                self.biomarkers.append(MDP())
            elif bio == "APD90":
                self.biomarkers.append(APD90())
            elif bio == "APD60":
                self.biomarkers.append(APD60())
            else:
                raise ValueError(f'Unrecognized biomarker `{bio}`')

    def __str__(self) -> str:
        bio_str = ' , '.join(map(str, list(map(type, self.biomarkers))))
        return f'id: {self.id} | win: {self.window} | target: {self.target} | file: {self.file}| {bio_str}'

    def _required_data_full(self) -> list:
        required_data = []
        for bm in self.biomarkers:
            for data_name in bm.required_data():
                if data_name not in required_data:
                    required_data.append(data_name)
        return required_data


    def dry(self, experiment: Experiment) -> None:
        print("Find biomarkers for the following:")
        for bm in self.biomarkers:
            print(str(type(bm)))
        print(f'Data is accessed with following types: `{"`, `".join(self._required_data_full())}`')
        print(f'Using experiment: `{experiment}`')

    def run(self, experiment: Experiment) -> None:
        # Collect list of all needed data from biomarkers
        names = self._required_data_full()
        # get data through the experiment needed for the biomarkers
        for idx in range(0, experiment.cells):
            # get data through the experiment needed for the biomarkers
            experiment.get_data(names, idx)


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
    print('\n--script-running--')

    # Run all experiments
    experiment.dry(models)

    # Calculate biomarkers for each `target` instance
    biomarkers.dry(experiment)

    # Go through each calibration condition
    print(calibration)


if __name__ == '__main__':
    run()
