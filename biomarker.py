import numpy as np
import experiment as exp
import scipy.signal
import matplotlib.pyplot as plt # temp debug
import utility

TIME = 'time'
VM = 'Vm'
CALSIUM = 'Cai'
STIM = 'iStim'
FORCE = "Force"
LSARC = "Lsarc"

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
        self.mcp_idx = 0

class Window:
    def __init__(self, original_data: dict) -> None:
        self.data = original_data
        self.top = np.ndarray([]) # For each peak
        self.bot = np.ndarray([]) # For each peak
        self.win = {} # Our windowed data (dictionary)
        self.mdp_all = None # All minimum action potentials, ie valleys
        self.mdp = np.ndarray([]) # Minimum action potentials, ie valleys
        self.is_stimulated = False # Detected if data is stimulated
        self._ap_beats = [] # views describing the beats based on Vm
        self._cai_beats = [] # views describing the beats based on Cai
        self.beat_count = 4

    def ap_beats(self) -> list:
        if not self._ap_beats:
            self._make_win_ap_beats()
        return self._ap_beats

    def cai_beats(self) -> list:
        if not self._cai_beats:
            self._make_cai_beats()
        return self._cai_beats

    def _make_win_ap_beats(self) -> None:
        # TODO add some minimum distance for the peaks (or valleys) so we don't get something weird, should depend on dt
        # TODO using 0 for threshold, which is arbitrary, should prob use something more meaningful
        self.mdp_all, _ = scipy.signal.find_peaks(-self.data[VM], threshold=0.0)

        # find beats defined from bottom-to-bottom, amount described in beat_count, detected from Vm
        for i in range(self.beat_count):
            start_idx = self.mdp_all[-1-self.beat_count + i]
            end_idx = self.mdp_all[-1-self.beat_count + i + 1]
            beat = Beat()
            for key in self.data:
                # Make view of each data name per beat
                beat.data[key] = self.data[key][start_idx:end_idx]
            self._ap_beats.append(beat)

        if STIM in self.data:
            if 1 < len(np.unique(self.data[STIM])):
                self.is_stimulated = True
        self._make_ap_top()


    def _make_ap_top(self) -> None:
        if self.is_stimulated:
            for beat in self._ap_beats:
                beat.bot_idx = np.nonzero(0 < np.diff(beat.data[STIM]))[0]
                beat.top_idx, _ = scipy.signal.find_peaks(beat.data[VM])
        else:
            raise ValueError('Only implemented for stimulated')

    def _make_cai_beats(self) -> None:
        bot_cai_all, _ = scipy.signal.find_peaks(-self.data[CALSIUM])

        for i in range(self.beat_count):

            start_idx = bot_cai_all[-1- self.beat_count + i]
            end_idx = bot_cai_all[-1- self.beat_count + i + 1]

            cai_beat = Beat()
            for key in self.data:
                # Make view of each data name per beat
                cai_beat.data[key] = self.data[key][start_idx:end_idx]
            cai_beat.top_idx = int(np.argmax(cai_beat.data[CALSIUM]))
            self._cai_beats.append(cai_beat)
        self._make_MCP()

    def _make_MCP(self) ->None:
        # Soglia (from matlab) = Minimiums with a condition -> mcp = minimium condition point
        lag = 21

        threshold = 1.2

        for beat in self.cai_beats():
            cai = beat.data[CALSIUM] #start ja end on bot indexejä
            lag_values = cai[lag:]
            now_values = cai[:-lag]

            location = np.argwhere(lag_values > now_values*threshold)
            beat.mcp_idx = int(location[0])


class Max_Cai:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'Max_Cai'

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def calculate(self, window: Window) -> float:
        max_cai = np.zeros(window.beat_count)
        i = 0
        for beat in window.cai_beats():
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
        min_cai = np.zeros(window.beat_count)
        i = 0
        for beat in window.cai_beats():
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
        for beat in window.cai_beats():
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
        all_values = np.zeros(window.beat_count)
        for i in range(window.beat_count):
            all_values[i] = window.ap_beats()[i].data[VM][0]
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
        for beat in window.ap_beats():
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
        for beat in window.ap_beats():
            value = np.divide(np.diff(beat.data[VM]), np.diff(beat.data[TIME]))
            dVM= np.concatenate((dVM, value))

        min_distance = APD_N(90).calculate(window)*1000 #s to ms
        Locations_of_peaks, _ = scipy.signal.find_peaks(dVM,distance=min_distance)
        dv_dt = dVM[Locations_of_peaks]
        dv_dt_max = np.divide(np.sum(dv_dt), len(dv_dt))
        return dv_dt_max


class APA:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'APA'

    def required_data(self) -> list:
        return [TIME, VM, STIM]

    def calculate(self, window: Window) -> float:
        max = -np.inf
        for beat in window.ap_beats():
            beat_max = np.max(beat.data[VM])
            if beat_max > max:
                max = beat_max
        return max-MDP().calculate(window)


class Peak:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'Peak'

    def required_data(self) -> list:
        return [TIME, VM, STIM]

    def calculate(self, window: Window) -> float:
        ap_values = []
        for beat in window.ap_beats():
            ap_values.append(np.max(beat.data[VM]))

        return np.mean(ap_values)


class RTNM:
    def __init__(self, N: int,  M: int) -> None:
        self.N = N
        self.M = M

    def __str__(self) -> str:
        return 'RT'+ str(self.N)+str(self.M)

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def calculate(self, window: Window) -> float:
        N = self.N/100
        M = self.M/100
        risetime = []

        for beat in window.cai_beats():
            start_index = beat.mcp_idx
            end_index = beat.top_idx

            cai = beat.data[CALSIUM]
            time_window = beat.data[TIME]
            height = cai[end_index] - cai[start_index]
            JM = np.argwhere(cai[start_index:end_index] >= cai[start_index] + M * height)[0]
            JN = np.argwhere(cai[start_index:end_index] <= cai[start_index] + N * height)[-1]
            time = time_window[start_index + JM] - time_window[start_index + JN]
            risetime.append(time)

        return np.mean(risetime)

class DTNM:
    def __init__(self, N: int,  M: int) -> None:
        self.N = N
        self.M = M
    def __str__(self) -> str:
        return 'DT'+ str(self.N)+str(self.M)
    def required_data(self) -> list:
        return [TIME, CALSIUM]
    def calculate(self, window: Window) -> float:
        N = self.N/100
        M = self.M/100
        dectime = []
        cai_beats = window.cai_beats()
        for i in range(window.beat_count-1):
            beat = cai_beats[i]
            next_beat = cai_beats[i+1]
            start_index = beat.top_idx
            end_index = len(beat.data[CALSIUM])

            cai = np.append(beat.data[CALSIUM], next_beat.data[CALSIUM][0])
            t = np.append(beat.data[TIME], next_beat.data[TIME][0])

            JN = np.argwhere(cai[start_index:end_index] <= cai[end_index] + N * cai[start_index])[0]
            JM = np.argwhere(cai[start_index:end_index] >= cai[end_index] + M * cai[start_index])[-1]
            time = t[start_index + JM] - t[start_index + JN]
            dectime.append(time)

        return np.mean(dectime)

class RTNPeak:
    def __init__(self, N: int) -> None:
        self.N = N

    def __str__(self) -> str:
        return 'RT'+ str(self.N)+'Peak'

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def calculate(self, window: Window) -> float:
        N = self.N / 100
        rtpeak = []

        for beat in window.cai_beats():
            start_index = beat.mcp_idx
            end_index = beat.top_idx

            cai = beat.data[CALSIUM]
            t = beat.data[TIME]

            height = cai[end_index] - cai[start_index]
            JN = np.argwhere(cai[start_index:end_index] <= cai[start_index] + N * height)[-1]
            time = t[end_index] - t[start_index + JN]
            rtpeak.append(time)

        return np.mean(rtpeak)


class CAI_DURATION:
    def __init__(self) -> None:
        pass
    def __str__(self) -> str:
        return 'CAI_DURATION'

    def required_data(self) -> list:
        return [TIME, CALSIUM]
    def calculate(self, window: Window) -> float:

        cai_beats = window.cai_beats()
        duration = []
        for i in range(window.beat_count-1):
            beat = cai_beats[i]
            next_beat = cai_beats[i+1]

            start_index = beat.top_idx
            end_index = len(beat.data[CALSIUM])
            mcp = beat.mcp_idx

            cai = np.append(beat.data[CALSIUM], next_beat.data[CALSIUM][0])
            t = np.append(beat.data[TIME], next_beat.data[TIME][0])

            mcp_otherside = start_index + np.argwhere(cai[start_index:end_index] >= cai[mcp])[-1]
            time = t[mcp_otherside] - t[mcp]
            duration.append(time)

        return np.mean(duration)


class CTDN:
    def __init__(self, N: int) -> None:
        self.N = N

    def __str__(self) -> str:
        return 'CTD' + str(self.N)

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def calculate(self, window: Window) -> float:
        ctdn = []
        N_ = 1-self.N/100
        cai_beats = window.cai_beats()

        for i in range(window.beat_count - 1): #n-1 first beats
            beat = cai_beats[i]
            next_beat = cai_beats[i + 1]

            start_index = beat.mcp_idx
            end_index = len(beat.data[CALSIUM])

            cai = np.append(beat.data[CALSIUM], next_beat.data[CALSIUM][0])
            t = np.append(beat.data[TIME], next_beat.data[TIME][0])

            height = np.argwhere(cai[start_index:end_index] >= cai[start_index] + N_*(np.max(cai[start_index:end_index] - cai[start_index])))
            time = t[start_index+height[-1]] - t[start_index+height[0]]
            ctdn.append(time)

        return np.mean(ctdn)


class APD_N:
    '''action potential duration at N% repolarization'''
    def __init__(self, N: int) -> None:
        self.N = N

    def __str__(self) -> str:
        return 'APD' + str(self.N)

    def required_data(self) -> list:
        return [TIME, VM, STIM]

    def calculate(self, window: Window) -> float:
        all_values = np.zeros(window.beat_count)
        i = 0
        beat: Beat
        for beat in window.ap_beats():
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


class Rate_AP:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'Rate_AP'

    def required_data(self) -> list:
        return [TIME, VM, STIM]

    def calculate(self, window: Window) -> float:
        seconds_in_min = 60
        scale = 1000
        return seconds_in_min/float(CL().calculate(window)/scale)

class RAPP_APD:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'RAPP_APD'

    def required_data(self) -> list:
        return [TIME, VM, STIM]

    def calculate(self, window: Window) -> float: #toimii
        apd30 = APD_N(30).calculate(window)
        apd40 = APD_N(40).calculate(window)
        apd70 = APD_N(70).calculate(window)
        apd80 = APD_N(80).calculate(window)

        return (apd30-apd40)/(apd70-apd80)

class peakTension:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'peakTension'

    def required_data(self) -> list:
        return [FORCE]

    def calculate(self, window: Window) -> float:
        maxtension = []
        for beat in window.ap_beats():
            force = beat.data[FORCE]
            locs, _ = scipy.signal.find_peaks(force)
            values = force[locs]
            maxtension = np.concatenate((maxtension, values))

        return np.mean(maxtension)

class cellShortPerc:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return 'cellShortPerc'

    def required_data(self) -> list:
        return [TIME, VM, LSARC]

    def calculate(self, window: Window) -> float:
        cellshort = []
        max_Lsarc = -np.inf
        for beat in window.ap_beats():
            Lsarc = beat.data[LSARC]
            locs, _ = scipy.signal.find_peaks(-Lsarc)
            values = Lsarc[locs]
            cellshort = np.concatenate((cellshort, values))

            if np.max(Lsarc) > max_Lsarc:
                max_Lsarc = np.max(Lsarc)

        Cellshort = np.mean(cellshort)
        cellshortperc = 100*Cellshort/max_Lsarc
        return cellshortperc

BIOMARKERS = {'MDP': MDP(),
              'Max_Cai': Max_Cai(),
              'Min_Cai': Min_Cai(),
              'Rate_Cai': Rate_Cai(),
              'CL': CL(),
              'dv_dt_max': dv_dt_max(),
              'APA': APA(),
              'Peak': Peak(),
              'RT1050': RTNM(10, 50),
              'RT1090': RTNM(10, 90),
              'DT9010': DTNM(90,10),
              'RT10Peak': RTNPeak(10),
              'APD10': APD_N(10),
              'APD20': APD_N(20),
              'APD30': APD_N(30),
              'APD40': APD_N(40),
              'APD50': APD_N(50),
              'APD60': APD_N(60),
              'APD70': APD_N(70),
              'APD80': APD_N(80),
              'APD90': APD_N(90),
              }


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
            results = ['nan'] * len(self.biomarkers)
            for i in range(len(self.biomarkers)):
                try:
                    results[i] = str(self.biomarkers[i].calculate(data))
                except:
                    results[i] = 'nan'

            results = [str(bm.calculate(data)) for bm in self.biomarkers]
            # Remove following comments to print out biomarkers for each cell
            #for name, result in zip(header, results):
            #    print(f"{name}: {result}")


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
