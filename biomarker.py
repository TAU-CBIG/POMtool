import numpy as np
import experiment as exp

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

    def dry(self, experiment: exp.Experiment) -> None:
        print("Find biomarkers for the following:")
        for bm in self.biomarkers:
            print(str(type(bm)))
        print(f'Data is accessed with following types: `{"`, `".join(self._required_data_full())}`')
        print(f'Using experiment: `{experiment}`')

    def run(self, experiment: exp.Experiment) -> None:
        # Collect list of all needed data from biomarkers
        names = self._required_data_full()
        # get data through the experiment needed for the biomarkers
        for idx in range(0, experiment.cells):
            # get data through the experiment needed for the biomarkers
            experiment.get_data(names, idx)

