import numpy as np
import experiment as exp
import scipy.signal
import matplotlib.pyplot as plt # temp debug
import utility

TIME = 'time'
VM = 'Vm'
CALSIUM = 'Cai'
STIM = 'iStim'

CSV_SEPARATOR = ', '
CSV_ENDLINE = '\n'

class Beat:
    def __init__(self) -> None:
        self.data = {}
        self.bot_idx = 0
        self.top_idx = 0
        self.mdp = []

class Cai_Beat:
    def __init__(self) -> None:
        self.data = {}
        self.bot_idx = 0
        self.top_idx = 0
        self.end_idx =0
        self.start_idx=0
        self.mcp = []

class Window:
    def __init__(self, original_data: dict) -> None:
        self.data = original_data
        self.top = np.ndarray([]) # For each peak
        self.bot = np.ndarray([]) # For each peak
        self.win = {} # Our windowed data (dictionary)
        self.mdp_all = None # All minimum action potentials, ie valleys
        self.mdp = np.ndarray([]) # Minimum action potentials, ie valleys
        self.is_stimulated = False # Detected if data is stimulated
        self.is_win_calculated = False # flag to set when win is calculated
        self.is_top_calculated = False # flag to set when top is calculated
        self.beats = [] # views describing the peaks
        self.cai_beats = []
        self.beat_count = 4
        self.is_cai_peaks_calculated = False
        self.is_mcp_calculated = False

    def make_win(self) -> None:
        '''Makes window indexes based on the given data, call to make sure win exists'''
        if self.is_win_calculated:
            return
        self.is_win_calculated = True

        # TODO add some minimum distance for the peaks (or valleys) so we don't get something weird, should depend on dt
        # TODO using 0 for threshold, which is arbitrary, should prob use something more meaningful
        self.mdp_all, _ = scipy.signal.find_peaks(-self.data[VM], threshold=0.0)

        # find beats defined from bottom-to-bottom, amount described in beat_count, detected from Vm
        for i in range(0, self.beat_count):
            start_idx = self.mdp_all[-1-self.beat_count + i]
            end_idx = self.mdp_all[-1-self.beat_count + i + 1]
            beat = Beat()
            for key in self.data:
                # Make view of each data name per beat
                beat.data[key] = self.data[key][start_idx:end_idx]
            self.beats.append(beat)

        if STIM in self.data:
            if 1 < len(np.unique(self.data[STIM])):
                self.is_stimulated = True


    def make_top(self) -> None:
        if self.is_top_calculated:
            return
        self.is_top_calculated = True
        self.make_win()

        if self.is_stimulated:
            for beat in self.beats:
                beat.bot_idx = np.nonzero(0 < np.diff(beat.data[STIM]))[0]
                beat.top_idx, _ = scipy.signal.find_peaks(beat.data[VM])
        else:
            raise ValueError('Only implemented for stimulated')

    def make_cai_peaks(self) -> None:
        if self.is_cai_peaks_calculated:
            return
        self.is_cai_peaks_calculated = True
        self.make_win()

        bot_cai_all, _ = scipy.signal.find_peaks(-self.data[CALSIUM])

        for i in range(0, self.beat_count):

            start_idx = bot_cai_all[-1- self.beat_count + i]
            end_idx = bot_cai_all[-1- self.beat_count + i + 1]

            cai_beat = Beat()
            for key in self.data:
                # Make view of each data name per beat
                cai_beat.data[key] = self.data[key][start_idx:end_idx]
            cai_beat.top_idx = int(np.argmax(cai_beat.data[CALSIUM]))
            self.cai_beats.append(cai_beat)

    def make_MCP(self) ->None:
        # Soglia (from matlab) = Minimiums with a condition -> mcp = minimium condition point

        if self.is_mcp_calculated:
            return
        self.is_mcp_calculated = True
        self.make_cai_peaks()
        lag = 21

        threshold = 1.2

        for beat in self.cai_beats:
            cai = beat.data[CALSIUM] #start ja end on bot indexejä
            lag_values = cai[lag:]
            now_values = cai[:-lag]

            location = np.argwhere(lag_values > now_values*threshold)
            beat.mcp = int(location[0])


class Max_Cai:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'Max_Cai'

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def calculate(self, window: Window) -> float:
        max_cai = np.zeros(len(window.cai_beats))
        i = 0
        for beat in window.cai_beats:
            max_cai[i] = np.max(beat.data[CALSIUM])
            i += 1
        return np.mean(max_cai)


class Min_Cai:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'Min_Cai'

    def required_data(self) -> list:

        return [TIME, CALSIUM]

    def calculate(self, window: Window) -> float:
        min_cai = np.zeros(len(window.cai_beats))
        i = 0
        for beat in window.cai_beats:
            min_cai[i] = np.min(beat.data[CALSIUM])
            i += 1

        return np.mean(min_cai)


class Rate_Cai:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'Rate_Cai'

    def required_data(self) -> list:

        return [TIME, VM, STIM, CALSIUM]  # makewin tarvii noi muutkin

    def calculate(self, window: Window) -> float:

        CLCa = []
        for beat in window.cai_beats:
            CLCa.append(beat.data[TIME][beat.top_idx])
        CLCa = np.diff(CLCa)
        Freq = np.divide(1000, CLCa)
        return Freq.mean()

class MDP:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'MDP'

    def required_data(self) -> list:
        return [TIME, VM, STIM]

    def calculate(self, window: Window) -> float:
        all_values = np.zeros(len(window.beats))
        for i in range(window.beat_count):
            all_values[i] = window.beats[i].data[VM][0]
        return all_values.mean()

class CL:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'CL'

    def required_data(self) -> list:
        return [TIME, VM, STIM]

    def calculate(self, window: Window) -> np.ndarray:
        cl = []
        for beat in window.beats:
            cl.append(beat.data[TIME][beat.mdp])
        cl = np.diff(cl)

        return np.divide(np.sum(cl), len(cl))

class dv_dt_max:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'dV_dt_max'

    def required_data(self) -> list:
        return [TIME, VM, STIM]

    def calculate(self, window: Window) -> float:
        dVM = []
        for beat in window.beats:
            value = np.divide(np.diff(beat.data[VM]), np.diff(beat.data[TIME]))
            dVM= np.concatenate((dVM, value))

        min_distance = APD_N(90).calculate(window)*1000 #s to ms
        Locations_of_peaks, _ = scipy.signal.find_peaks(dVM,distance=min_distance)
        dv_dt = dVM[Locations_of_peaks]
        dv_dt_max = np.divide(np.sum(dv_dt), len(dv_dt))
        return dv_dt_max

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
        all_values = np.zeros(len(window.beats))
        i = 0
        beat: Beat
        for beat in window.beats:
            top = beat.data[VM][beat.top_idx]
            bot = beat.data[VM][beat.bot_idx]

            # Scale to N% from the top
            value_height = ((1 - self.N/100) * (top-bot)) + bot

            # Two values at given height, (start and end)
            at_height = np.argwhere(beat.data[VM] > value_height).ravel()
            all_values[i] = beat.data[TIME][at_height[-1]] - beat.data[TIME][at_height[0]]
            i += 1
            # Debug printing if you want to check what is actually happening
            # plt.plot(beat.data[TIME],beat.data[VM])
            # plt.plot(beat.data[TIME][beat.bot_idx], beat.data[VM][beat.bot_idx], 'x')
            # plt.plot(beat.data[TIME][beat.top_idx], beat.data[VM][beat.top_idx], 'o')
            # plt.plot(beat.data[TIME][[at_height[1], at_height[-1]]], [value_height, value_height])
            # plt.show()

        return all_values.mean()

APD_VALUES_OF_N = [60, 90]
BIOMARKERS = {'MDP': MDP()
              } | { str(APD_N(val)): APD_N(val) for val in APD_VALUES_OF_N}

class Biomarkers:
    def __init__(self, args, patch_idx: int, patch_count: int) -> None:
        self.window_start = args[0].get('window_start', None)
        self.window_end = args[0].get('window_end', None)
        self.target = args[0]['target']
        self.file = args[0]['file']
        self.patch_file = utility.append_patch(self.file, patch_idx, patch_count)
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
        for idx in experiment.patch:
            # get data through the experiment needed for the biomarkers
            data = Window(experiment.get_data(names, idx))
            data.make_top()
            results = ['nan'] * len(self.biomarkers)
            for i in range(len(self.biomarkers)):
                try:
                    results[i] = str(self.biomarkers[i].calculate(data))
                except:
                    results[i] = 'nan'

            results = [str(bm.calculate(data)) for bm in self.biomarkers]
            all_results.append(results)
            file_name = f'{experiment.get_directory(idx)}/{self.file}'
            file = open(file_name, 'w')
            file.write(CSV_SEPARATOR.join(header) + CSV_ENDLINE)
            file.write(CSV_SEPARATOR.join(results) + CSV_ENDLINE)
        file_name = f'{experiment.cwd}/{self.patch_file}'
        file = open(file_name, 'w')
        file.write(CSV_SEPARATOR.join(['directory'] + header) + CSV_ENDLINE)
        idx = 0
        for res in all_results:
            file.write(experiment.get_directory(idx) + CSV_SEPARATOR + CSV_SEPARATOR.join(res) + CSV_ENDLINE)
            idx += 1
