import scimath.units.api as API
import scimath.units.SI as SI

def append_patch(name, id, count) -> str:
    return f'{name}-{id + 1}-{count}' if count > 1 else name

FORCE = "Force"
TIME = "time"
POTENTIAL = "potential"
LENGTH = "length"
MOLAR = "molar"
FREQUENCY = "frequency"
FORCE_PER_AREA = "force_per_area"
UNITLESS = "unitless"
VOLT_PER_SECOND = "volt_per_second"
DEFAULT = "default"

base_units = {TIME: {DEFAULT: SI.second, "s": SI.second, "ms": SI.milli * SI.second, "min": 60 * SI.second},
         POTENTIAL: {DEFAULT: SI.volt, "V": SI.volt, "mV": SI.volt*SI.milli, "uV": SI.micro*SI.volt},
         FORCE: {DEFAULT: SI.newton,"N": SI.newton, "mN": SI.milli*SI.newton},
         LENGTH: {DEFAULT: SI.meter,'m': SI.meter, "mm": SI.milli*SI.meter},
         MOLAR: {DEFAULT: SI.mole,"mol": SI.mole, "umol" : SI.mole*SI.micro, "mmol" : SI.mole*SI.milli},
         UNITLESS : {DEFAULT: SI.none, "unitless": SI.none},
        }
derived_units = {FORCE_PER_AREA: {DEFAULT: base_units[FORCE][DEFAULT]/base_units[LENGTH][DEFAULT]**2, "mN/mm2":(SI.milli*SI.newton)/((SI.milli*SI.meter)**2)},
                VOLT_PER_SECOND: {DEFAULT: base_units[POTENTIAL][DEFAULT]/base_units[TIME][DEFAULT], "mV/ms": (SI.milli*SI.volt)/(SI.milli*SI.second), "V/s": SI.volt / SI.second},
                    FREQUENCY: {DEFAULT: 1/base_units[TIME][DEFAULT],"Hz": 1/base_units[TIME]["s"], "bpm": 1/base_units[TIME]["min"]},
                  }

units = base_units | derived_units

def initialize_default_unit_of():

    default_unit_of = {}
    unit_to_scimath = {}
    default_option = {}

    for category in units.keys():
        units_category = units[category]
        default_unit = units_category[DEFAULT]

        for unit_name in units_category:
            if units_category[unit_name]== default_unit:
                default_option[category] = unit_name
            default_unit_of[unit_name] = default_unit
            unit_to_scimath[unit_name] = units_category[unit_name]

    return default_unit_of, unit_to_scimath, default_option


default_unit_of, unit_to_scimath, default_option = initialize_default_unit_of()


def convert_to_default(data, unit): # -> np.ndarray OR float
    from_unit = unit_to_scimath[unit]
    to_unit = default_unit_of[unit]
    return API.convert(data, from_unit, to_unit)


def convert_from_default(data, unit): # -> np.ndarray OR float
    from_unit = default_unit_of[unit]
    to_unit = unit_to_scimath[unit]
    return API.convert(data, from_unit, to_unit)
