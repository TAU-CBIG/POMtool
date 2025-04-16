import model
import numpy as np
import scipy.stats as sstats

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

    def dry(self, models: model.Models) -> None:
        print(f"Manifest {self.cwd + '/' + self.manifest_file_name}: ")
        print(self._internal_run(models, model.Model.dry))

    def run(self, models: model.Models) -> None:
        manifest = self._internal_run(models, model.Model.run)
        with open(self.cwd + '/' + self.manifest_file_name, 'w') as f:
            f.write(manifest)

    def _internal_run(self, models: model.Models, method) -> str:
        self.model: model.Model = models.model(self.model_id)
        # generate all parameters
        parameters = self._generate_parameters()
        manifest = self._generate_manifest(parameters)

        for idx in range(0, self.cells):
            full_path = self._get_directory(idx)
            method(self.model, full_path, parameters[idx,:])
        return manifest

    def get_data(self, names: list, idx: int) -> dict:
        return self.model.get_data(self._get_directory(idx), names)
