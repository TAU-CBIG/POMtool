import log
import model
import numpy as np
import scipy.stats as sstats
import utility

class Experiment:
    def __init__(self, args, patch_idx: int, patch_count: int) -> None:
        self.name = args['name']
        self.id = args['id']
        self.model_id = args['model']
        self.cwd = utility.append_patch(args['cwd'], patch_idx, patch_count)
        self.parametrization = args['parametrization']
        self.cells = args['cells']
        self.parameter_count = args['parameter_count']
        self.manifest_file_name = utility.append_patch(args['manifest'], patch_idx, patch_count)
        self.equation = args['equation'] if 'equation' in args else ""
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

    def get_id(self, idx) -> str:
        str_length = len(str(self.cells))
        return self.name.replace("#", str(idx+1).rjust(str_length, "0"))

    def get_directory(self, idx) -> str:
        return f'{self.cwd}/{self.get_id(idx)}'

    def _generate_parameters(self) -> np.ndarray:
        x = np.ndarray([])
        if self.parametrization == 'latin_hybercube':
            sampler = sstats.qmc.LatinHypercube(d=self.parameter_count, seed=0)
            x = sampler.random(n=self.cells)
        else:
            raise ValueError(f'parametrization method "{self.parametrization}" not recognized')
        return x if not self.equation else eval(f'{self.equation}')

    def _generate_manifest(self, parameters: np.ndarray) -> str:
        manifest = ''
        # run for each parameter
        for idx in self.patch:
            directory = self.get_id(idx)
            manifest_line = [directory]
            for par in parameters[idx,:]:
                manifest_line.append(str(par))
            manifest += (', '.join(manifest_line)) + ";\n"
        return manifest

    def empty_run(self, models: model.Models) -> None:
        def nop(arg1, arg2, arg3):
            pass
        self._internal_run(models, nop)

    def dry(self, models: model.Models) -> None:
        log.print_info(f"Manifest {self.cwd + '/' + self.manifest_file_name}: ")
        log.print_info(self._internal_run(models, model.Model.dry))

    def run(self, models: model.Models) -> None:
        manifest = self._internal_run(models, model.Model.run)
        with open(self.cwd + '/' + self.manifest_file_name, 'w') as f:
            f.write(manifest)

    def _internal_run(self, models: model.Models, method) -> str:
        self.model: model.Model = models.model(self.model_id)
        # generate all parameters
        parameters = self._generate_parameters()
        manifest = self._generate_manifest(parameters)

        for idx in self.patch:
            full_path = self.get_directory(idx)
            method(self.model, full_path, parameters[idx,:])
        return manifest

    def get_data(self, required_names: list, optional_names: list, idx: int) -> dict:
        return self.model.get_data(self.get_directory(idx), required_names, optional_names)
