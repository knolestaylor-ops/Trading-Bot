import pathlib

class ParquetWriter:
    def __init__(self):
        self.path = pathlib.Path(__file__).parent.absolute()