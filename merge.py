import experiment as exp
import biomarker as bio
import calibration as cal
import shutil
import pathlib

class Merge:
    def __init__(self, content, patches, force, dry) -> None:
        self.content = content
        self.patches = patches
        self.force = force
        self.dry = dry

    def merge_experiments(self) -> None:
        experiment_base = exp.Experiment(self.content['experiment'][0], 0, 1)
        copy_instructions = []
        manifest_files = []
        manifest_base_file = experiment_base.cwd + '/' + experiment_base.manifest_file_name
        for i in range(self.patches):
            experiment = exp.Experiment(self.content['experiment'][0], i, self.patches)
            manifest_files.append(experiment.cwd + '/' + experiment.manifest_file_name)
            for j in experiment.patch:
                copy_instructions.append([experiment.get_directory(j), experiment_base.get_directory(j)])
        if self.dry:
            for ci in copy_instructions:
                print(f'Copy `{ci[0]}` into `{ci[1]}`')
            print(f'Manifest({manifest_base_file}):\n  ' + '\n  '.join(manifest_files))
        else:
            if pathlib.Path(experiment_base.cwd).exists():
                if self.force:
                    shutil.rmtree(experiment_base.cwd, ignore_errors=True)
                else:
                    raise FileExistsError('Directory already created, use --force or delete the directory')

            for ci in copy_instructions:
                shutil.copytree(ci[0], ci[1], dirs_exist_ok=True)

            with open(manifest_base_file, 'w') as f:
                for file_name in manifest_files:
                    with open(file_name, 'r') as file:
                        f.write(file.read())

        
    def merge_biomarkers(self) -> None:
        cwd_base = exp.Experiment(self.content['experiment'][0], 0, 1).cwd + '/'
        biomarkers_base_file = cwd_base + bio.Biomarkers(self.content['biomarkers'], 0, 1).patch_file
        biomarkers_file = []
        for i in range(self.patches):
            cwd = exp.Experiment(self.content['experiment'][0], i, self.patches).cwd + '/'
            biomarkers_file.append(cwd + bio.Biomarkers(self.content['biomarkers'], i, self.patches).patch_file)
        if self.dry:
            print(f'File({biomarkers_base_file}):\n  ' + '\n  '.join(biomarkers_file))
        else:
            with open(biomarkers_base_file, 'w') as f:
                header_done = False
                for file_name in biomarkers_file:
                    with open(file_name, 'r') as file:
                        if header_done:
                            file.readline()
                        f.write(file.read())
                        header_done = True



    def merge_calibration(self) -> None:
        raise NotImplementedError("Calibration merge has not yet been implemented")

