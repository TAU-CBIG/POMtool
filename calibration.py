import csv
import math
import pathlib
import utility
import experiment as exp


def convert_to_default(value: float, unit: str):
    try:
        return utility.convert_to_default(value, unit)
    except:
        raise KeyError(f"Calibration tried to use unit '{unit}'. Hint: Check your 'range.csv' units. We only support units: {list(utility.unit_to_scimath.keys())}")


class Protocol:
    def __init__(self, args: dict, cwd: str, patch_idx: int, patch_count: int) -> None:
        self.method = args['protocol']
        self.contains_fail_path = 'fail_path' in args.keys()
        self.contains_success_path = 'success_path' in args.keys()
        self.patch_idx = patch_idx
        self.patch_count = patch_count
        self.cwd = cwd
        self.fail_path = None
        self.success_path = None
        self.input_data_path = None
        self.biomarker_units = {}
        self.is_setup_data = False
        self.fail_dict_name = None
        self.ranges = {}
        self.range_units = {}
        self.is_ranges_converted = False
        self.is_biomarkers_converted = False

        if self.contains_fail_path:
            self.fail_dict_name = args['fail_path']

        self.success_dict_name = None
        if self.contains_success_path:
            self.success_dict_name = args['success_path']

        self.input_data_path = None
        if 'input_data_path' in args.keys():
            self.input_data_path = args['input_data_path']


    def setup_data(self) ->None:
        if self.is_setup_data:
            return
        self.is_setup_data = True

        if self.contains_fail_path:
            self.fail_path = self.cwd + '/' + utility.append_patch(self.fail_dict_name, self.patch_idx, self.patch_count)
            pathlib.Path(self.fail_path).parent.mkdir(exist_ok=True, parents=True)
            with open(self.fail_path, 'w'):
                pass #truncate

        if self.contains_success_path:
            self.success_path = self.cwd + '/' + utility.append_patch(self.success_dict_name, self.patch_idx, self.patch_count)
            pathlib.Path(self.success_path).parent.mkdir(exist_ok=True, parents=True)
            with open(self.success_path, 'w'):
                pass #truncate

        if self.method == 'range':
            with open(self.input_data_path, 'r') as file: #(example_range.csv)
                reader = csv.reader(file)
                header = []
                units = {}

                #Parse names (first line)
                for val in next(reader):
                    if '(' not in val and ')' not in val:
                        val += '(default)'
                    elif '(' not in val or ')' not in val:
                        raise KeyError(f"Fix the limits to format 'biomarker_name (unit)' or 'biomarker_name' instead of '{val}'")

                    val = val.strip()
                    name, unit = val.split("(")
                    name = name.strip()
                    units[name] = unit[:-1].strip()
                    header.append(name.strip())

                #Parse min values (second line)
                min_values = []
                for value in next(reader):
                    value = value.strip()
                    if value == "" or value=="none":
                        value = "-inf"
                    min_values.append(float(value))
                #Parse max values (third line)
                max_values = []
                for value in next(reader):
                    value = value.strip()
                    if value == "" or value == "none":
                        value = "inf"
                    max_values.append(float(value))

                values = tuple(zip(min_values, max_values))
                self.ranges = dict(zip(header, values))
                self.range_units = units
                for key, val in self.ranges.items():
                    if val[0] > val[1]:
                        raise ValueError(f'For range in `{self.input_data_path}` with key `{key}`, minimum({val[0]}) is larger than maximum({val[1]})')

    def run(self, values: dict) -> bool:
        ret_val = False
        if self.method == 'nonan':
            ret_val = self.nonan_method(values)
        elif self.method == 'range':
            self.ranges, self.range_units = self.convert_ranges(self.biomarker_units, self.ranges, self.range_units)
            values = self.convert_biomarkers(values)
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

    def convert_ranges(self,biomarker_units: dict, ranges: dict, range_units: dict) -> tuple[dict, dict]: #convert ranges to the default unit
        if self.is_ranges_converted:
            return ranges, range_units
        self.is_ranges_converted = True
        for name in range_units.keys():
            unit = range_units[name]
            if unit == utility.DEFAULT:  # If default -> same unit as biomarker
                unit = biomarker_units[name]
            range_units[name] = unit  # Might not need this

            min_value = convert_to_default(ranges[name][0], unit)
            max_value = convert_to_default(ranges[name][1], unit)

            ranges[name] = (min_value, max_value)
        return ranges, range_units

    def convert_biomarkers(self, biomarkers: dict) -> dict: #convert biomarkers to the default unit
        if self.is_biomarkers_converted:
            return biomarkers
        self.is_biomarkers_converted = True

        bio_units = {}
        for name in biomarkers.keys():
            value = biomarkers[name]
            if type(value) != float:
                bio_units[name] = value
                continue
            unit = self.biomarker_units[name]
            bio_units[name] = convert_to_default(float(value), unit)
        return bio_units


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
            for protocol in self.protocols:
                protocol.setup_data()
                protocol.biomarker_units = units

            # Parse other lines (lines with numbers)
            for line in reader:
                for protocol in self.protocols:
                    looks = {header[0]: line[0]} #line 0 is str but others need to be a floating point
                    for name, value in zip(header[1:], line[1:]):
                        looks[name] = float(value)

                    if not protocol.run(looks):
                        break
