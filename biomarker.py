import numpy as np
import experiment as exp
import scipy.signal
import matplotlib.pyplot as plt # temp debug

TIME = 'time'
VM = 'Vm'
CALSIUM = 'Cai'
STIM = 'iStim'

CSV_SEPARATOR = ', '
CSV_ENDLINE = '\n'

class Window:
    # TODO: remove use of range, it actually creates copy and not view
    def __init__(self, original_data: dict) -> None:
        self.data = original_data
        self.top = np.ndarray([])
        self.bot = np.ndarray([])
        self.win = range(0) 
        self.mdp_all = None # All minimum action potentials, ie valleys
        self.ap = np.ndarray([])  # Maximum action potentials, ie peaks
        self.mdp = np.ndarray([]) # Minimum action potentials, ie valleys
        self.is_stimulated = False
        self.is_top_calculated = False
        self.is_win_calculated = False

    def make_win(self) -> None:
        '''Makes window indexes based on the given data, call to make sure win exists'''
        if self.is_win_calculated:
            return
        self.is_win_calculated = True
        numberOfPeaks = 4
        # TODO add some minimum distance for the peaks (or valleys) so we don't get something weird, should depend on dt
        self.mdp_all, _ = scipy.signal.find_peaks(-self.data['Vm'])
        extra_front_space = 600
        self.win = range(self.mdp_all[-1-numberOfPeaks] - extra_front_space, self.mdp_all[-1])
        self.mdp = self.mdp_all[-1-numberOfPeaks:-1] - self.win.start

        self.ap, _ = scipy.signal.find_peaks(self.data['Vm'][self.win])
        self.ap += self.win.start
        plt.plot(self.data['time'][self.ap], self.data['Vm'][self.ap], 'x')
        self.ap -= self.win.start

        if 'iStim' in self.data:
            if 1 < len(np.unique(self.data['iStim'])):
                self.is_stimulated = True


    def make_top(self) -> None:
        if self.is_top_calculated:
            return
        self.is_top_calculated = True
        self.make_win()

        if self.is_stimulated:
            self.bot = np.nonzero(0 < np.diff(self.data['iStim'][self.win]))[0]
            plt.plot(self.data['time'][self.win][self.bot], self.data['Vm'][self.win][self.bot], 'x')
            self.top = self.ap
        else:
            raise ValueError('Only implemented for stimulated')
        plt.plot(self.data['time'][self.win], self.data['Vm'][self.win])


class MDP:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'MDP'

    def required_data(self) -> list:
        return [TIME, VM, STIM]

    def calculate(self, window: Window) -> float:
        print(window.mdp)
        return window.data['Vm'][window.win][window.mdp].mean()

class APD_N:
    '''action potential duration at N% repolarization'''
    def __init__(self, N: int) -> None:
        self.N = N

    def __str__(self) -> str:
        return 'APD' + str(self.N)

    def required_data(self) -> list:
        return [TIME, VM, STIM]

    def calculate(self, window: Window) -> float:
        window.make_top()
        top = window.data['Vm'][window.win][window.top]
        bot = window.data['Vm'][window.win][window.bot]
        heights = (1 - (self.N/100))*(top - bot) + bot
        all_values = np.zeros(len(heights))

        for i in range(len(heights)):
            height = heights[i]
            pulse_win = range(window.mdp[i], window.mdp[i+1] if i < len(heights) - 1 else window.win.stop - window.win.start)
            at_height = np.argwhere(window.data['Vm'][window.win][pulse_win] > height).ravel()
            print(height)
            print(at_height)
            print(at_height[-1])
            print(at_height[0])
            all_values[i] = window.data['time'][window.win][at_height[-1]] - window.data['time'][window.win][at_height[0]]

        return all_values.mean()

APD_VALUES_OF_N = [60, 90]
BIOMARKERS = {'MDP': MDP()
              } | { str(APD_N(val)): APD_N(val) for val in APD_VALUES_OF_N}

class Biomarkers:
    def __init__(self, args) -> None:
        self.window_start = args[0].get('window_start', None)
        self.window_end = args[0].get('window_end', None)
        self.target = args[0]['target']
        self.file = args[0]['file']
        self.biomarkers = []
        for i in range(1,len(args)):
            bio = args[i]['biomarker']
            if not bio in BIOMARKERS:
                raise ValueError(f'Unrecognized biomarker `{bio}`')
            self.biomarkers.append(BIOMARKERS[bio])

    def __str__(self) -> str:
        bio_str = ' , '.join(map(str, list(map(type, self.biomarkers))))
        return f'id: {self.id} | target: {self.target} | file: {self.file}| {bio_str}'

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
        print(f'Would write to file: `{self.file}`')

    def run(self, experiment: exp.Experiment) -> None:
        # Collect list of all needed data from biomarkers
        names = self._required_data_full()
        header = [str(bm) for bm in self.biomarkers]
        all_results = []
        # get data through the experiment needed for the biomarkers
        for idx in range(0, experiment.cells):
            # get data through the experiment needed for the biomarkers
            data = Window(experiment.get_data(names, idx))
            data.make_top()

            results = [str(bm.calculate(data)) for bm in self.biomarkers]
            all_results.append(results)
            file_name = f'{experiment.get_directory(idx)}/{self.file}'
            file = open(file_name, 'w')
            file.write(CSV_SEPARATOR.join(header) + CSV_ENDLINE)
            file.write(CSV_SEPARATOR.join(results) + CSV_ENDLINE)
        file_name = f'{experiment.cwd}/{self.file}'
        file = open(file_name, 'w')
        file.write(CSV_SEPARATOR.join(['directory'] + header) + CSV_ENDLINE)
        idx = 0
        for res in all_results:
            file.write(experiment.get_directory(idx) + CSV_SEPARATOR + CSV_SEPARATOR.join(res) + CSV_ENDLINE)
            idx += 1
