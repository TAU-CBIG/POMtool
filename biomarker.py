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
        self.biomarkers = {}

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
        self.beat_count = 9
        self.ap_bot_calculated = False

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
        # TODO using 0 for threshold(ie height limit), which is arbitrary, should prob use something more meaningful
        self.mdp_all, _ = scipy.signal.find_peaks(-self.data[VM], height=0.0)

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

        for beat in self._ap_beats:
            top_idx, _ = scipy.signal.find_peaks(beat.data[VM])
            try:
                beat.top_idx = top_idx[0]
            except:
                beat.top_idx = top_idx

    def make_ap_bot(self) -> None:
        # Only needed for APD_N, but as it is needed for each, we store these in window to avoid recalculation
        if self.ap_bot_calculated:
            return
        self.ap_bot_calculated = True

        if self.is_stimulated:
            for beat in self._ap_beats:
                beat.bot_idx = np.nonzero(0 < np.diff(beat.data[STIM]))[0] + 1
        else:
            for beat in self._ap_beats:
                Vm = beat.data[VM]
                t = beat.data[TIME]
                #In matlab code threshold was µV
                threshold = utility.convert_to_default(-10,"uV")

                DDendind = np.min(np.argwhere(Vm > threshold))

                DDendtime = t[DDendind]
                fit_window_ind = round(2*(DDendind+1)/3)

                poly = np.polyfit(t[:fit_window_ind], Vm[:fit_window_ind], 1)
                BOT = poly[0]*DDendtime+poly[1]
                idxPertBOT = np.argwhere(t < DDendtime)
                Vm_shorter = Vm[idxPertBOT]
                idxBOT = np.max(np.argwhere(Vm_shorter <= BOT))
                beat.bot_idx = idxBOT



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
        lag = 20

        threshold = 1.2

        for beat in self.cai_beats():
            cai = beat.data[CALSIUM] #start ja end on bot indexejä
            lag_values = cai[lag:]
            now_values = cai[:-lag]

            location = np.argwhere(lag_values >= now_values*threshold)
            beat.mcp_idx = int(location[0])


class BiomarkerBase:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return "undefined"

    def required_data(self) -> list:
        raise NotImplementedError()

    def optional_data(self) -> list:
        return []

    def return_type(self) -> str:
        raise NotImplementedError()

    def calculate(self, window: Window) -> float:
        raise NotImplementedError()


class Max_Cai(BiomarkerBase):
    def __str__(self) -> str:
        return 'Max_Cai'

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def return_type(self) -> str:
        return utility.MOLAR

    def calculate(self, window: Window) -> float:
        max_cai = np.zeros(window.beat_count)
        i = 0
        for beat in window.cai_beats():
            max_cai[i] = np.max(beat.data[CALSIUM])
            i += 1
        return np.mean(max_cai)


class Min_Cai(BiomarkerBase):
    def __str__(self) -> str:
        return 'Min_Cai'

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def return_type(self) -> str:
        return utility.MOLAR

    def calculate(self, window: Window) -> float:
        min_cai = np.zeros(window.beat_count)
        i = 0
        for beat in window.cai_beats():
            min_cai[i] = np.min(beat.data[CALSIUM])
            i += 1

        return np.mean(min_cai)


class Rate_Cai(BiomarkerBase):
    def __str__(self) -> str:
        return 'Rate_Cai'

    def required_data(self) -> list:
        return [TIME, VM, CALSIUM]

    def return_type(self) -> str:
        return utility.FREQUENCY

    def calculate(self, window: Window) -> float:
        CLCa = []
        for beat in window.cai_beats():
            CLCa.append(beat.data[TIME][beat.top_idx])
        CLCa = np.diff(CLCa)
        Freq = 1/CLCa
        return Freq.mean()

class MDP(BiomarkerBase):
    def __str__(self) -> str:
        return 'MDP'

    def required_data(self) -> list:
        return [TIME, VM]

    def return_type(self) -> str:
        return utility.POTENTIAL

    def calculate(self, window: Window) -> float:
        all_values = np.zeros(window.beat_count)
        for i in range(window.beat_count):
            all_values[i] = window.ap_beats()[i].data[VM][0]
        return all_values.mean()

class CL(BiomarkerBase):
    def __str__(self) -> str:
        return 'CL'

    def required_data(self) -> list:
        return [TIME, VM]

    def return_type(self) -> str:
        return utility.TIME

    def calculate(self, window: Window) -> float:
        cl = []
        for beat in window.ap_beats():
            cl.append(beat.data[TIME][0])
        cl = np.diff(cl)

        return np.mean(cl)

class dv_dt_max(BiomarkerBase):
    def __str__(self) -> str:
        return 'dv_dt_max'

    def required_data(self) -> list:
        return [TIME, VM]

    def return_type(self) -> str:
        return utility.VOLT_PER_SECOND

    def calculate(self, window: Window) -> float:
        dV_dt = []
        for beat in window.ap_beats():
            value = np.divide(np.diff(beat.data[VM]), np.diff(beat.data[TIME]))
            dV_dt.append(np.max(value))

        return np.mean(dV_dt)


class APA(BiomarkerBase):
    def __str__(self) -> str:
        return 'APA'

    def required_data(self) -> list:
        return [TIME, VM]

    def return_type(self) -> str:
        return utility.POTENTIAL

    def calculate(self, window: Window) -> float:
        max = -np.inf
        for beat in window.ap_beats():
            beat_max = np.max(beat.data[VM])
            if beat_max > max:
                max = beat_max
        return max-MDP().calculate(window)


class Peak(BiomarkerBase):
    def __str__(self) -> str:
        return 'Peak'

    def required_data(self) -> list:
        return [TIME, VM]

    def return_type(self) -> str:
        return utility.POTENTIAL

    def calculate(self, window: Window) -> float:
        ap_values = []
        for beat in window.ap_beats():
            ap_values.append(np.max(beat.data[VM]))

        return np.mean(ap_values)


class RTNM(BiomarkerBase):
    def __init__(self, N: int, M: int) -> None:
        super().__init__()
        self.N = N
        self.M = M

    def __str__(self) -> str:
        return 'RT'+ str(self.N)+str(self.M)

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def return_type(self) -> str:
        return utility.TIME

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

class DTNM(BiomarkerBase):
    def __init__(self, N: int, M: int) -> None:
        super().__init__()
        self.N = N
        self.M = M

    def __str__(self) -> str:
        return 'DT'+ str(self.N)+str(self.M)

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def return_type(self) -> str:
        return utility.TIME

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

class RTNPeak(BiomarkerBase):
    def __init__(self, N) -> None:
        super().__init__()
        self.N = N

    def __str__(self) -> str:
        return 'RT'+ str(self.N)+'Peak'

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def return_type(self) -> str:
        return utility.TIME

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


class CAI_DURATION(BiomarkerBase):
    def __str__(self) -> str:
        return 'CAI_DURATION'

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def return_type(self) -> str:
        return utility.TIME

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


class CTDN(BiomarkerBase):
    def __init__(self, N: int) -> None:
        super().__init__()
        self.N = N

    def __str__(self) -> str:
        return 'CTD' + str(self.N)

    def required_data(self) -> list:
        return [TIME, CALSIUM]

    def return_type(self) -> str:
        return utility.TIME

    def calculate(self, window: Window) -> float: #TMP: Change this to match APD_N
        ctdn = []
        N_ = 1-self.N/100
        cai_beats = window.cai_beats()

        for i in range(window.beat_count - 1):
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


class APD_N(BiomarkerBase):
    '''action potential duration at N% repolarization'''
    def __init__(self, N: int) -> None:
        super().__init__()
        self.N = N

    def __str__(self) -> str:
        return 'APD' + str(self.N)

    def required_data(self) -> list:
        return [TIME, VM]

    def optional_data(self) -> list:
        return [STIM] # This will change how ap_bot_idx is calculate

    def return_type(self) -> str:
        return utility.TIME

    def calculate(self, window: Window) -> float:
        def vector_point_calc(b: Beat, h1, h2, value) -> float:
            x1 =np.array([b.data[TIME][h1], b.data[VM][h1]])
            x2 = np.array([b.data[TIME][h2], b.data[VM][h2]])

            vec = x2-x1
            k = (value-x1[1])/vec[1]
            vec2 = k*vec
            return x1[0] + vec2[0]

        window.make_ap_bot() # Ensure that we have bot idx
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
            t0 = vector_point_calc(beat, at_height[0]-1, at_height[0], value_height)
            t1 = vector_point_calc(beat, at_height[-1], at_height[-1]+1, value_height)
            all_values[i] = t1-t0
            beat.biomarkers[str(self)] = all_values[i]
            i += 1


            # Debug printing if you want to check what is actually happening
            # plt.plot(beat.data[TIME],beat.data[VM])
            # plt.plot(beat.data[TIME][beat.bot_idx], beat.data[VM][beat.bot_idx], 'x')
            # plt.plot(beat.data[TIME][beat.top_idx], beat.data[VM][beat.top_idx], 'o')

            # plt.plot([t0, t1], [value_height, value_height])
            # plt.show()
            #In matlab it takes maximium peak and we take first peak

        return all_values.mean()


class Rate_AP(BiomarkerBase):
    def __str__(self) -> str:
        return 'Rate_AP'

    def required_data(self) -> list:
        return [TIME, VM]

    def return_type(self) -> str:
        return utility.BEATS_PER_X

    def calculate(self, window: Window) -> float:
        return 1/CL().calculate(window)

class RAPP_APD(BiomarkerBase):
    def __str__(self) -> str:
        return 'RAPP_APD'

    def required_data(self) -> list:
        return [TIME, VM]

    def return_type(self) -> str:
        return utility.UNITLESS

    def calculate(self, window: Window) -> float: #toimii
        values = []
        def get_ap(win: Window, N: int):
            name = str(APD_N(N))
            if str(name) in beat.biomarkers:
                return beat.biomarkers[name]
            else:
                return APD_N(N).calculate(win)
        for beat in window.ap_beats():
            apd30 = get_ap(window, 30)
            apd40 = get_ap(window, 40)
            apd70 = get_ap(window, 70)
            apd80 = get_ap(window, 80)
            values.append((apd30-apd40)/(apd70-apd80))

        return np.mean(values)

class peakTension(BiomarkerBase):
    def __str__(self) -> str:
        return 'peakTension'

    def required_data(self) -> list:
        return [FORCE]

    def return_type(self) -> str:
        return utility.FORCE_PER_METER

    def calculate(self, window: Window) -> float:
        maxtension = []
        for beat in window.ap_beats():
            force = beat.data[FORCE]
            locs, _ = scipy.signal.find_peaks(force)
            values = force[locs]
            maxtension = np.concatenate((maxtension, values))

        return np.mean(maxtension)

class cellShortPerc(BiomarkerBase):
    def __str__(self) -> str:
        return 'cellShortPerc'

    def required_data(self) -> list:
        return [TIME, VM, LSARC]

    def return_type(self) -> str:
        return utility.UNITLESS

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

class relaxTime50(BiomarkerBase):
    def __str__(self) -> str:
        return 'relaxTime50'

    def required_data(self) -> list:
        return [TIME, VM, LSARC, FORCE]

    def return_type(self) -> str:
        return utility.TIME

    def calculate(self, window: Window) -> float:
        relaxTime50Buf = np.zeros(window.beat_count-1)
        i = 0

        stepTol = 0.5e-4
        maxTol = 5e-4
        minTol = 1e-4


        for beat_idx in range(window.beat_count-1):
            beat = window.ap_beats()[beat_idx]
            next_beat = window.ap_beats()[beat_idx+1]
            t = np.concatenate((beat.data[TIME], next_beat.data[TIME]))
            frc = np.concatenate((beat.data[FORCE], next_beat.data[FORCE]))
            top = beat.top_idx

            next_top = next_beat.top_idx+len(beat.data[TIME])-1

            relaxTime50Buf[i] = self.computeContrRT50(t, t[top], t[next_top], frc, minTol, maxTol, stepTol)


            i += 1
        return np.mean(relaxTime50Buf)

    def computeContrRT50(self, t, tStartRT50, tStopRT50, Frc, min, max, step) -> float:
        min_tol = min
        max_tol = max
        step_tol = step

        tt = np.argwhere((tStartRT50 <= t) & (t <= tStopRT50))
        ts = tt[0][0]
        te = tt[-1][0]
        tlc = t[ts:te]
        frct = Frc[ts:te]
        pkt = np.max(frct)
        ppp = np.argmax(frct)
        pkt_time = tlc[ppp]

        count = 0

        rel50 = []
        while min_tol <= max_tol:
            min_tol = min_tol + step_tol*count
            rel50 = np.argwhere(np.abs(frct[ppp:]-0.5*pkt)<=min_tol)
            if len(rel50) >= 1:
                rel50 = rel50[0]
                break
            count +=1
        halfreltime = tlc[ppp + rel50]
        RT50 = (halfreltime - pkt_time)



        return RT50

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
              'CAI_DURATION': CAI_DURATION(),
              'CTD30': CTDN(30),
              'CTD50': CTDN(50),
              'CTD90': CTDN(90),
              'Rate_AP': Rate_AP(),
              'RAPP_APD': RAPP_APD(),
              'peakTension': peakTension(),
              'cellShortPerc': cellShortPerc(),
              'APD10': APD_N(10),
              'APD20': APD_N(20),
              'APD30': APD_N(30),
              'APD40': APD_N(40),
              'APD50': APD_N(50),
              'APD60': APD_N(60),
              'APD70': APD_N(70),
              'APD80': APD_N(80),
              'APD90': APD_N(90),
              "relaxTime50": relaxTime50()
              }


class Biomarkers:
    def __init__(self, args, patch_idx: int, patch_count: int) -> None:
        self.target = args[0]['target']
        self.file = args[0]['file']
        self.patch_file = utility.append_patch(self.file, patch_idx, patch_count)
        self.biomarkers = []
        self.biomarker_units = {}
        for i in range(1,len(args)):
            bio = args[i]['biomarker']
            if "unit" in args[i]:
                unit = args[i]['unit']
            else:
                unit = "default"

            if not bio in BIOMARKERS:
                raise ValueError(f'Unrecognized biomarker `{bio}`')
            self.biomarkers.append(BIOMARKERS[bio])
            self.biomarker_units[bio] = unit

    def __str__(self) -> str:
        bio_str = ' , '.join(map(str, list(map(type, self.biomarkers))))
        return f'target: {self.target} | file: {self.file}| {bio_str}'

    def _required_data_full(self) -> list:
        required_data = []
        for bm in self.biomarkers:
            for data_name in bm.required_data():
                if data_name not in required_data:
                    required_data.append(data_name)
        return required_data

    def _optional_data_full(self) -> list:
        optional_data = []
        for bm in self.biomarkers:
            for data_name in bm.optional_data():
                if data_name not in optional_data:
                    optional_data.append(data_name)
        return optional_data

    def dry(self, experiment: exp.Experiment) -> None:
        print("Find biomarkers for the following:")
        for bm in self.biomarkers:
            print(str(type(bm)))
        print(f'Data is accessed with following types: `{"`, `".join(self._required_data_full())}`')
        print(f'Using experiment: `{experiment}`')
        print(f'Would write to file: `{self.file}`')

    def run(self, experiment: exp.Experiment) -> None:
        # Collect list of all needed data from biomarkers
        names_required = self._required_data_full()
        names_optional = self._optional_data_full()
        header = [str(bm)+f" ({self.biomarker_units[str(bm)]})" for bm in self.biomarkers]
        all_results = []
        # get data through the experiment needed for the biomarkers
        for idx in experiment.patch:
            # get data through the experiment needed for the biomarkers
            data = Window(experiment.get_data(names_required, names_optional, idx))
            results = ['nan'] * len(self.biomarkers)
            for i in range(len(self.biomarkers)):
                try:
                    value = self.biomarkers[i].calculate(data)
                except:
                    value = float('nan')
                unit = self.biomarker_units[str(self.biomarkers[i])]
                type = self.biomarkers[i].return_type()
                if unit == "default":
                    unit = utility.default_option[type]
                    self.biomarker_units[str(self.biomarkers[i])] = unit
                    header[i] = unit
                results[i] = str(utility.convert_from_default(value, unit))

            # Remove following comments to print out biomarkers for each cell
            #for bm, result in zip(self.biomarkers, results):
            #    print(f"{str(bm)}: {result} {self.biomarker_units[str(bm)]}")


            all_results.append(results)
            file_name = f'{experiment.get_directory(idx)}/{self.file}'
            file = open(file_name, 'w')
            file.write(CSV_SEPARATOR.join(header) + CSV_ENDLINE)
            file.write(CSV_SEPARATOR.join(results) + CSV_ENDLINE)
        file_name = f'{experiment.cwd}/{self.patch_file}'
        file = open(file_name, 'w')
        file.write(CSV_SEPARATOR.join(['directory'] + header) + CSV_ENDLINE)
        idx = experiment.patch.start
        for res in all_results:
            file.write(experiment.get_id(idx) + CSV_SEPARATOR + CSV_SEPARATOR.join(res) + CSV_ENDLINE)
            idx += 1
