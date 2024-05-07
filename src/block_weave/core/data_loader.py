# Text utf-8 encoded files e.g. .md, .txt, .py

class DataLoader:

    def __init__(self):
        pass

    @staticmethod
    def read_utf8_file(filepath):
        # read markdown or txt or .py like files in utf-8
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()

    @staticmethod
    def write_utf8_file(filepath, content):
        # write markdown or txt like files in utf-8
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)
