import csv

class Protocol:
    def __init__(self, args) -> None:
        self.method = args['protocol']

    def run(self, values) -> bool:
        print('values', values)
        return True

class Calibration:
    def __init__(self, args) -> None:
        self.biomarker_file = args[0]['file']
        self.protocols = []
        for arg in args[1:]:
            self.protocols.append(Protocol(arg))

    def __str__(self) -> str:
        return 'No printing in calibration, sorry'

    def run(self) -> None:
        with open(self.biomarker_file) as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            print('header: ', header)
            for line in reader:
                for protocol in self.protocols:
                    looks = dict(zip(header, line))
                    protocol.run(looks)

