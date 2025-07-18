from . import experiment as exp
from . import biomarker as bio
from . import utility
from . import log
import shutil
import pathlib

class Merge:
    def __init__(self, content, patches, force, dry) -> None:
        self.content = content
        self.patches = patches
        self.force = force
        self.dry = dry

    def merge_experiments(self) -> None:
        experiment_base = exp.Experiment(self.content['experiment'][0], 0, 1, 0)
        copy_instructions = []
        manifest_files = []
        manifest_base_file = experiment_base.cwd + '/' + experiment_base.manifest_file_name
        for i in range(self.patches):
            experiment = exp.Experiment(self.content['experiment'][0], i, self.patches, 0)
            manifest_files.append(experiment.cwd + '/' + experiment.manifest_file_name)
            for j in experiment.patch:
                copy_instructions.append([experiment.get_directory(j), experiment_base.get_directory(j)])
        if self.dry:
            for ci in copy_instructions:
                log.print_info(f'Copy `{ci[0]}` into `{ci[1]}`')
            log.print_info(f'Manifest({manifest_base_file}):\n  ' + '\n  '.join(manifest_files))
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
        cwd_base = exp.Experiment(self.content['experiment'][0], 0, 1, 0).cwd + '/'
        biomarkers_base_file = cwd_base + bio.Biomarkers(self.content['biomarkers'], 0, 1).patch_file
        biomarkers_file = []
        for i in range(self.patches):
            cwd = exp.Experiment(self.content['experiment'][0], i, self.patches, 0).cwd + '/'
            biomarkers_file.append(cwd + bio.Biomarkers(self.content['biomarkers'], i, self.patches).patch_file)
        if self.dry:
            log.print_info(f'File({biomarkers_base_file}):\n  ' + '\n  '.join(biomarkers_file))
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
        files = []
        for val in self.content['calibration']:
            if 'fail_path' in val:
                files.append(val['fail_path'])
            if 'success_path' in val:
                files.append(val['success_path'])

        cwd_base = exp.Experiment(self.content['experiment'][0], 0, 1, 0).cwd + '/'

        for i in range(self.patches):
            cwd = exp.Experiment(self.content['experiment'][0], i, self.patches, 0).cwd + '/'
            for file in files:
                patch_path = utility.append_patch(cwd+file, i, self.patches)
                new_path = cwd_base + file
                with open(patch_path, 'r') as patch_file:
                    with open(new_path, 'a') as new_file:
                        new_file.write(patch_file.read())
