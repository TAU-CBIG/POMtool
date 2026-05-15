from . import log
from . import model
import numpy as np
import scipy.stats as sstats
from . import utility
import pathlib

class Experiment:
    @staticmethod
    def names_from_manifest(filename):
        l = []
        with open(filename) as f:
            content = f.read()
            vals = [line.strip().split(',')[0] for line in content.split(';')]
            return vals[0:-1]

    @staticmethod
    def makeEq(args, name):
        name_min = name + '_min'
        name_mid = name + '_mid'
        name_max = name + '_max'
        a = args[name_min] if name_min in args else None
        b = args[name_mid] if name_mid in args else None
        c = args[name_max] if name_max in args else None
        if a and b and c:
            return f'np.heaviside(0.5-x,0)*(2*({b}-{a})*x+{a}) + (1 - np.heaviside(0.5-x,0))*(2*({c}-{b})*(x-0.5)+{b})'
        elif a and c:
            return f'({c}-{a})*x + {a}'
        else:
            return args[name] if name in args else None

    def __init__(self, args, patch_idx: int, patch_count: int, seed: int) -> None:
        self.id = args['id']
        self.model_id = args['model']
        self.cwd = utility.append_patch(args['cwd'], patch_idx, patch_count)
        self.parametrization = args['parametrization']
        if self.parametrization == 'latin_hybercube':
            self.cells = args['cells']
            self.name = args['name']
            self.parameter_count = args['parameter_count']
        if self.parametrization == 'sensitivity':
            self.sweep_size = args['sweep_size']
            self.parameter_count = args['parameter_count']
            self.cells = self.sweep_size * self.parameter_count
            self.name = args['name']
        if self.parametrization == 'file':
            if 'name' in args:
                raise ValueError('`name` is not used for `file`-parameterization, names come from file')
            self.parameter_file = args['file']
            self.parameter_selection = args['selection'] if 'selection' in args else ''

            accepted_parameters = lambda x : True

            if self.parameter_selection != '':
                if not pathlib.Path(self.parameter_selection).exists():
                    raise ValueError(f'File {self.parameter_file} missing')
                with open(self.parameter_selection, 'r') as f:
                    valid_parameters = set(f.read().replace('\n', ';').replace('\r', '').split(';'))
                    accepted_parameters = lambda x : x in valid_parameters

            if not pathlib.Path(self.parameter_file).exists():
                raise ValueError(f'File {self.parameter_file} missing')
            with open(self.parameter_file, 'r') as f:
                parameters = list(filter(None, f.read().replace('\n', ';').replace('\r', '').split(';')))
                self.full_parameter_names = []
                self.final_parameters = []
                for par in parameters:
                    par_vals = par.split(',')
                    name = par_vals[0]
                    if not accepted_parameters(name):
                        continue
                    self.full_parameter_names.append(name)
                    self.final_parameters.append(par_vals[1:])
                self.cells = len(self.full_parameter_names)
                self.parameter_count = len(self.final_parameters[0])


        self.parameter_names = [None] * self.parameter_count
        self.parameter_defaults = [None] * self.parameter_count
        for i in range(self.parameter_count):
            par_name_i = f'par_{i+1}_name'
            par_dflt_i = f'par_{i+1}_default'
            self.parameter_names[i] = args[par_name_i] if par_name_i in args else str(i)
            self.parameter_defaults[i] = args[par_dflt_i] if par_dflt_i in args else None
        self.manifest_file_name = utility.append_patch(args['manifest'], patch_idx, patch_count)
        base_equation = Experiment.makeEq(args, 'equation')
        self.equations = []
        for i in range(self.parameter_count):
            eq = Experiment.makeEq(args, f'par_{i+1}_equation')
            self.equations.append(eq if eq else base_equation)

        self.seed = seed
        if patch_idx < 0:
            raise ValueError(f"Patch index cannot be less than zero (was `{patch_idx}`)")
        if patch_idx == patch_count:
            raise ValueError(f"Patch index too large: was equal to patch count (was `{patch_idx}`)")
        if patch_idx > patch_count:
            raise ValueError(f"Patch index too large: index (was `{patch_idx}`) greater to patch count (was `{patch_count}`)")

        # First patches are longer, if patch sizes cannot be divided equally
        patch_length_small = int(self.cells/patch_count)
        patch_mod = self.cells % patch_count
        patch_length = patch_length_small + (1 if patch_idx < patch_mod else 0)
        patch_start = patch_length_small * patch_idx + min(patch_idx, patch_mod)

        # Patch range
        self.patch = range(patch_start, patch_start + patch_length)


    def __str__(self) -> str:
        return self.id

    def _get_id_enumerate(self, idx) -> str:
        str_length = len(str(self.cells))
        return self.name.replace("#", str(idx+1).rjust(str_length, "0"))

    def _generate_id_sensitivity(self, idx, parameters) -> str:
        return self.name \
            .replace("#", self.id_num_fun(parameters[idx, idx // self.sweep_size])) \
            .replace("%", self.parameter_names[idx // self.sweep_size])

    def init_get_id_sensitivity(self, parameters):
        uniq = np.unique(parameters)
        self.id_left_min_size = max(len(str(int(uniq[-1]))), len(str(int(uniq[0]))))
        for self.id_right_min_size in range(0, 128):
            s = np.char.mod(f'%.{self.id_right_min_size}f', uniq)
            same = s[1:] != s[0:-1]
            if same.all():
                break

        if (uniq[0] < 0.0).all():
            self.id_num_fun = lambda val : f'{"neg" if val < 0 else "pos"}_' + f'{{:.{self.id_right_min_size}f}}'.format(abs(val)).rjust(self.id_left_min_size + 1 + self.id_right_min_size, "0")
        else:
            self.id_num_fun = lambda val : f'{{:.{self.id_right_min_size}f}}'.format(val).rjust(self.id_left_min_size + 1 + self.id_right_min_size, "0")

    def get_id(self, idx) -> str:
        return f'{self.run_names[idx - self.patch.start]}'

    def get_directory(self, idx) -> str:
        return f'{self.cwd}/{self.get_id(idx)}'

    def _generate_parameters(self) -> np.ndarray:
        arr = np.ndarray([])
        if self.parametrization == 'latin_hybercube':
            sampler = sstats.qmc.LatinHypercube(d=self.parameter_count, seed=self.seed)
            arr = sampler.random(n=self.cells)
            for i in range(np.size(arr, 1)):
                if self.equations[i]:
                    x = arr[:, i]
                    arr[:, i] = eval(self.equations[i])
        elif self.parametrization == 'sensitivity':
            arr = np.ones((self.cells, self.parameter_count))/2.0
            sweep = np.arange(0, self.sweep_size, dtype=np.float64)/(self.sweep_size - 1)
            for i in range(self.parameter_count):
                start = i * self.sweep_size
                arr[start:(start+self.sweep_size), i] = sweep
                if self.equations[i]:
                    x = arr[:, i]
                    arr[:, i] = eval(self.equations[i])
                if self.parameter_defaults[i]:
                    arr[0:start, i] = self.parameter_defaults[i]
                    arr[(start+self.sweep_size):, i] = self.parameter_defaults[i]
        elif self.parametrization == 'file':
            arr = np.zeros((self.cells, self.parameter_count))
            for i in range(self.cells):
                arr[i, :] = [float(x) for x in self.final_parameters[i]]
        else:
            raise ValueError(f'Parametrization method "{self.parametrization}" not recognized')
        return arr

    def _generate_manifest(self, parameters: np.ndarray) -> str:
        if self.parametrization == 'latin_hybercube':
            get_id = lambda i : self._get_id_enumerate(i)
        elif self.parametrization == 'sensitivity':
            get_id = lambda i : self._generate_id_sensitivity(i, parameters)
            self.init_get_id_sensitivity(parameters)
        elif self.parametrization == 'file':
            get_id = lambda i : self.full_parameter_names[i]
        else:
            raise ValueError(f'Parametrization method "{self.parametrization}" not recognized')

        manifest = ''
        run_names = []
        # run for each parameter
        for idx in self.patch:
            directory = get_id(idx)
            run_names.append(directory)
            manifest_line = [directory]
            for par in parameters[idx,:]:
                manifest_line.append(str(par))
            manifest += (', '.join(manifest_line)) + ";\n"
        return manifest, run_names

    def empty_run(self, models: model.Models) -> None:
        def nop(arg1, arg2, arg3):
            pass
        self._internal_run(models, nop)

    def dry(self, models: model.Models) -> None:
        log.print_info(f"Manifest {self.cwd + '/' + self.manifest_file_name}: ")
        log.print_info(self._internal_run(models, model.Model.dry))

    def run(self, models: model.Models) -> None:
        if not self.patch:
            log.print_info("Patch has no job")
            return

        manifest = self._internal_run(models, model.Model.run)
        with open(self.cwd + '/' + self.manifest_file_name, 'w') as f:
            f.write(manifest)

    def _internal_run(self, models: model.Models, method) -> str:
        self.model: model.Model = models.model(self.model_id)
        # generate all parameters
        parameters = self._generate_parameters()
        manifest, self.run_names = self._generate_manifest(parameters)

        for idx in self.patch:
            full_path = self.get_directory(idx)
            method(self.model, full_path, parameters[idx,:])

        return manifest

    def get_data(self, required_names: list, optional_names: list, idx: int) -> dict:
        return self.model.get_data(self.get_directory(idx), required_names, optional_names)
