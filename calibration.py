import csv
import math
import pathlib
import utility
import experiment as exp

def convert_to(value: str):
    try:
        return float(value)
    except:
        return value

class Protocol:
    def __init__(self, args: dict, cwd: str, patch_idx: int, patch_count: int) -> None:
        self.method = args['protocol']
        self.contains_fail_path = 'fail_path' in args
        self.contains_success_path = 'success_path' in args
        if self.contains_fail_path:
            self.fail_path = cwd + '/' + utility.append_patch(args['fail_path'], patch_idx, patch_count)
            pathlib.Path(self.fail_path).parent.mkdir(exist_ok=True, parents=True)
            with open(self.fail_path, 'w'):
                pass #truncate

        if self.contains_success_path:
            self.success_path = cwd + '/' + utility.append_patch(args['success_path'], patch_idx, patch_count)
            pathlib.Path(self.success_path).parent.mkdir(exist_ok=True, parents=True)
            with open(self.success_path, 'w'):
                pass #truncate

        if self.method == 'range':
            self.input_data_path = args['input_data_path']
            with open(self.input_data_path, 'r') as file:
                reader = csv.reader(file)
                header = [val.strip() for val in next(reader)]
                min_values = [float(value) for value in next(reader)]
                max_values = [float(value) for value in next(reader)]
                values = tuple(zip(min_values, max_values))
                self.ranges = dict(zip(header, values))
                for key, val in self.ranges.items():
                    if val[0] > val[1]:
                        raise ValueError(f'For range in `{self.input_data_path}` with key `{key}`, minimum({val[0]}) is larger than maximum({val[1]})')

    def run(self, values: dict) -> bool:
        ret_val = False
        if self.method == 'nonan':
            ret_val = self.nonan_method(values)
        elif self.method == 'range':
            ret_val = self.range_method(values)
        else:
            raise RuntimeError('Protocol not defined')

        if ret_val:
            if self.contains_success_path:
                with open(self.success_path, 'a') as file:
                    file.write(values['directory'] + '\n')
        else:
            if self.contains_fail_path:
                with open(self.fail_path, 'a') as file:
                    file.write(values['directory'] + '\n')
        return ret_val

    def nonan_method(self, values: dict) -> bool:
        for _, val in values.items():
            if type(val) != float:
                continue
            if math.isnan(val):
                return False
            if math.isinf(val):
                return False
        return True

    def range_method(self, values: dict) -> bool:
        for key, val in values.items():
            if type(val) != float:
                continue
            if key not in self.ranges:
                continue
            min = self.ranges[key][0]
            max = self.ranges[key][1]
            if val < min or val > max:
                return False
        return True

class Calibration:
    def __init__(self, args, experiment: exp.Experiment, patch_idx: int, patch_count: int) -> None:
        self.biomarker_file = f"{experiment.cwd}/{utility.append_patch(args[0]['file'], patch_idx, patch_count)}"
        self.protocols = []
        for arg in args[1:]:
            self.protocols.append(Protocol(arg, experiment.cwd, patch_idx, patch_count))

    def __str__(self) -> str:
        return 'No printing in calibration, sorry'

    def run(self) -> None:
        with open(self.biomarker_file) as csvfile: # in example (biomarkers.csv)
            reader = csv.reader(csvfile)
            header = []
            units = {}

            # Parse biomarker header
            for val in next(reader):
                if "(" not in val:
                    header.append(val)
                    continue
                val = val.strip()
                name, unit = val.split("(")
                name = name.strip()
                units[name] = unit[:-1].strip()
                header.append(name)
            for line in reader:
                for protocol in self.protocols:
                    looks = dict(zip(header, [convert_to(value) for value in line]))
                    protocol.run(looks)
