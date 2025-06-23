import csv
import pathlib
import model as mod
import biomarker
import numpy as np
import utility
import hashlib


class LossFunction:
    def __init__(self, content: dict, model: mod.Model) -> None:
        self.content = content
        self.working_dir = content["cwd"]
        self.model = model
        self.bounds = None
        self.targets = {}
        self.target_units = {}
        self.bio_content = []
        self.dir_name = content["dir_name"]
        self.loss_calculation = None

    def setup(self) -> None:
        self.setup_target()
        self.setup_bio_content()

    def setup_target(self):
        if "target_file" not in self.content.keys():
            raise KeyError(f"Optimization needs targets.csv file in config")

        target_file = self.content["target_file"]
        with open(target_file) as csvfile:
            reader = csv.reader(csvfile)  # for biomarker targets
            header = []
            units = {}
            full_name = []

            # Parse biomarker names
            for val in next(reader):
                full_name.append(val)
                val = val.strip()
                name, unit = val.split("(")
                name = name.strip()
                units[name] = unit[:-1].strip()
                header.append(name)
            targets = {}
            ind = 0
            for val in next(reader):
                name = header[ind]
                targets[name] = float(val)
                ind += 1
            self.targets = targets
            self.target_units = units

    def setup_bio_content(self) -> None:
        bio_content = [self.content]

        for name in self.targets.keys():
            bio_content.append({"biomarker": name, "unit": self.target_units[name]})
        self.bio_content = bio_content

    def calculate_biomarkers(self, dir_name: pathlib.Path) -> dict:
        biomarkers = []
        for bio in self.targets.keys():
            biomarkers.append(biomarker.BIOMARKERS[bio])

        names_required = biomarker.Biomarkers.required_data_full(biomarkers)
        names_optional = biomarker.Biomarkers.optional_data_full(biomarkers)
        header = [str(bm) for bm in biomarkers]

        # get data through the experiment needed for the biomarkers
        data = biomarker.Window(self.model.get_data(str(dir_name), names_required, names_optional))
        results = ['nan'] * len(biomarkers)
        for i in range(len(biomarkers)):
            try:
                value = biomarkers[i].calculate(data)
            except:
                value = float('nan')
            unit = self.target_units[str(biomarkers[i])]
            return_type = biomarkers[i].return_type()
            if unit == utility.DEFAULT:
                unit = utility.default_option[return_type]
                self.target_units[str(biomarkers[i])] = unit
                header[i] = str(biomarkers[i])
            try:
                # convert units to same as in target.csv
                results[i] = utility.convert_from_default(value, self.target_units[str(biomarkers[i])])
            except:
                raise KeyError(
                    f"We do not support the requested biomarker unit '{unit}'. We support units: {list(utility.unit_to_scimath.keys())}")

        result_dict = dict(zip(header, results))
        return result_dict

    def get_dir_name(self, x: np.ndarray) -> pathlib.Path:
        h = hashlib.md5(repr(x).encode()).hexdigest()
        return pathlib.Path(self.working_dir) / pathlib.Path(self.dir_name) / pathlib.Path(h)

    @staticmethod
    def check_for_nans(biomarkers: dict) -> bool:
        for value in biomarkers.values():
            if np.isnan(value):
                return True
        return False

    @staticmethod
    def save_loss(loss: float, dir_name: pathlib.Path) -> None:
        file_name = f'{dir_name}/loss.txt'
        with open(file_name, "w") as file:
            file.write(str(loss))

    def run_loss(self, x: np.ndarray) -> float:
        dir_name = self.get_dir_name(x)

        # check if the calculation is already made earlier and if so use the result of that calculation
        file_name = dir_name / pathlib.Path("loss.txt")
        if file_name.exists():
            txt = file_name.read_text()
            if txt is not None:
                return float(txt)

        # Run the Cell model
        self.model.run(dir_name, x)
        # Calculate biomarkers
        biomarkers = self.calculate_biomarkers(dir_name)

        # If nans in biomarkers punish by adding loss
        if self.check_for_nans(biomarkers):
            loss = np.inf
        else:
            # Calculate loss for each biomarker
            loss = self.calculate_loss(biomarkers)

        # Save the loss
        self.save_loss(loss, dir_name)
        # Delete the generated data file
        # self.model.delete_data(dir_name)
        return loss

    def calculate_loss(self, biomarkers: dict) -> float:
        raise NotImplementedError("not implemented, dont call this. Call one of the LOSSFUNCTIONS")


class MseLoss(LossFunction):
    def __init__(self, content, model) -> None:
        self.type = "mse"
        super().__init__(content, model)

    def calculate_loss(self, biomarkers: dict) -> float:
        loss = 0
        for name in self.targets.keys():
            target_value = self.targets[name]
            model_value = biomarkers[name]
            loss += (model_value - target_value) ** 2
        loss /= len(self.targets.keys())

        return loss


LOSSFUNCTIONS = {
    "mse": MseLoss,
}
