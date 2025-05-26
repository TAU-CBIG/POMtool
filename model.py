import numpy as np
import os
import shutil
import subprocess
import scipy.io
import utility

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

    def get_data(self, directory: str, required_names: list, optional_names: list) -> dict:
        ret_data = {}
        # opencarp = np.genfromtxt(args.name, delimiter=' ')
        traces = {}
        headers = {}
        mat_files ={}

        names = set(required_names + optional_names)
        required = set(required_names)

        for name in names:
            if name not in self.vals:
                if name in required:
                    raise ValueError(f'Required value `{name}` not found from model')
                continue
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
            elif value_data['method'] == 'matlab':
                filename = f'{directory}/{value_data["file"]}'
                item_id = value_data["id"]
                if filename not in mat_files:
                    mat_files[filename] = scipy.io.loadmat(f'{directory}/{value_data["file"]}')
                ret_data[name] = mat_files[filename][item_id].flatten()
            else:
                raise ValueError(f'undefined method to read the data')
            if 'unit' in value_data.keys():
                unit= value_data["unit"]
                if unit not in utility.unit_to_scimath.keys():
                    raise KeyError(f"Input '{name}' has unit '{unit}' that we do not support. We support the following units: {list(utility.unit_to_scimath.keys())}" )
            else:
                raise ValueError(f"Unit of `{name}` not defined. We support the following units: {list(utility.unit_to_scimath.keys())}")
            ret_data[name] = utility.convert_to_default(ret_data[name], value_data["unit"])
        return ret_data

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
