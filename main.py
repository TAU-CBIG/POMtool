#!/usr/bin/env python3

import argparse
import yaml
import scipy.stats as sstats
import numpy as np
import os
import subprocess
import shutil
import matplotlib.pyplot as plt # temp debug

class Model:
    def __init__(self, full_args) -> None:
        self.exec = None
        self.base_directory = None
        self.param_key = ''
        self.pars = []
        self.vals = {}
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
            if 'val' in args:
                self.vals[args['val']] = args
            if 'base_directory' in args:
                if self.base_directory != None:
                    raise ValueError('Multiple model base directories defined.')
                self.base_directory = args['base_directory']
        if self.param_key == '':
            self.param_key = '%#%'
        if self.exec == None:
            raise ValueError('exec not defined')
        print("self.vals")
        print(self.vals)

    def __str__(self) -> str:
        return f"{self.exec} {' '.join(self.pars)}"

    def _create_command(self, parameters) -> list:
        # Replace parameters
        full_command = [self.exec]

        for command_par in self.pars:
            new_command_par = command_par
            idx = 1
            for param in parameters:
                to_replace = self.param_key.replace('#', str(idx))
                new_command_par = new_command_par.replace(to_replace, str(param))
                idx += 1
            full_command.append(new_command_par)
        return full_command

    def dry(self, cwd, parameters) -> None:
        command = self._create_command(parameters)
        print(f'dry run in {cwd} of\n    {" ".join(command)}')

    def run(self, current_wd, parameters) -> None:
        command = self._create_command(parameters)
        shutil.rmtree(current_wd, ignore_errors=True)
        if self.base_directory != None:
            shutil.copytree(self.base_directory, current_wd)
        else:
            os.makedirs(current_wd, exist_ok=True)
        cmd_file = open(f'{current_wd}/cmd.txt', 'w')
        stdout_file = open(f'{current_wd}/stdout.txt', 'w')
        stderr_file = open(f'{current_wd}/stderr.txt', 'w')
        cmd_file.write(' '.join(command))
        cmd_file.write('\n')

        subprocess.run(' '.join(command), shell=True, cwd=current_wd, stdout=stdout_file, stderr=stderr_file)


    def get_data(self, directory: str, names: list) -> dict:
        ret_data = {}
        # opencarp = np.genfromtxt(args.name, delimiter=' ')
        traces = {}
        headers = {}
        for name in names:
            if not name in self.vals:
                raise ValueError(f'`{name}`-val not found from model')
            value_data = self.vals[name]
            if value_data['method'] == 'binary':
                ret_data[name] = np.fromfile(f'{directory}/{value_data["file"]}')
            elif value_data['method'] == 'openCARP_trace':
                trace_file = f'{directory}/{value_data["file"]}'
                header_file = f'{directory}/{value_data["header_file"]}'
                if not trace_file in traces :
                    traces[trace_file] = np.genfromtxt(trace_file)
                    lines = open(header_file, 'r').readlines()
                    headers[header_file] = ['time'] + [line.replace('\n', '') for line in lines]
                idx = headers[header_file].index(value_data["header_name"])
                ret_data[name] = traces[trace_file][:, idx]
            else:
                raise ValueError(f'undefined method to read the data')
        return ret_data

    @staticmethod
    def get_binary_data(directory: str, value_data: dict) -> np.ndarray:
        return np.fromfile(f'{directory}/{value_data["file"]}')


class Models:
    def __init__(self, args) -> None:
        self.models = {}
        location = 0
        while location < len(args):
            tmp_args = [args[location]]
            id = args[location]['id']
            location += 1
            while location < len(args):
                if 'par' in args[location]:
                    tmp_args.append(args[location])
                elif 'val' in args[location]:
                    tmp_args.append(args[location])
                else:
                    break
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
        self.manifest_file_name = args['manifest']

    def __str__(self) -> str:
        return self.id

    def _get_directory(self, idx) -> str:
        str_length = len(str(self.cells))
        return f'{self.cwd}/{self.name.replace("#", str(idx+1).rjust(str_length, "0"))}'

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
        print(f"Manifest {self.cwd + '/' + self.manifest_file_name}: ")
        print(self._internal_run(models, Model.dry))

    def run(self, models: Models) -> None:
        manifest = self._internal_run(models, Model.run)
        with open(self.cwd + '/' + self.manifest_file_name, 'w') as f:
            f.write(manifest)

    def _internal_run(self, models: Models, method) -> str:
        self.model: Model = models.model(self.model_id)
        # generate all parameters
        parameters = self._generate_parameters()
        manifest = self._generate_manifest(parameters)

        for idx in range(0, self.cells):
            full_path = self._get_directory(idx)
            method(self.model, full_path, parameters[idx,:])
        return manifest

    def get_data(self, names: list, idx: int) -> dict:
        return self.model.get_data(self._get_directory(idx), names)

TIME = 'time'
VM = 'Vm'
CALSIUM = 'Ca'

class MDP:
    def __init__(self) -> None:
        pass

    def required_data(self) -> list:
        return [TIME, VM]

    def calculate(self, data) -> np.number:
        return np.number(1.0)


class APD90:
    def __init__(self) -> None:
        pass

    def required_data(self) -> list:
        return [TIME, VM]

    def calculate(self, data) -> np.number:
        return np.number(1.0)

class APD60:
    def __init__(self) -> None:
        pass

    def required_data(self) -> list:
        return [TIME, VM]

    def calculate(self, data) -> np.number:
        return np.number(1.0)


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
    if args.config:
        print(f'Using config `{args.config}`')
    with open(args.config, 'r') as f:
        content = yaml.safe_load(f)
    experiment = Experiment(content['experiment'][0])
    models = Models(content['model'])
    experiment = Experiment(content['experiment'][0])
    biomarkers = Biomarkers(content['biomarkers'])
    calibration = Calibration(content['calibration'])

    if args.dry:
        # Run all experiments
        experiment.dry(models)

        # Calculate biomarkers for each `target` instance
        biomarkers.dry(experiment)

        # Go through each calibration condition
        print(calibration)
    else:
        # Run all experiments
        experiment.dry(models)

        points = experiment.get_data(['time', 'Cai', 'Vm', 'iStim'], 0)
        plt.plot(points['time'], points['iStim'])
        plt.show()

        print("START biomarker")
        # Calculate biomarkers for each `target` instance
        biomarkers.run(experiment)


if __name__ == '__main__':
    run()
