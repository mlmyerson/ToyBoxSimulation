class Toy:
    def __init__(self, id, is_target, bin):
        self.id = id # unique per toy
        self.target = is_target # is a target toy for a child
        self.bin = bin # bin number of toy
        self.on_floor = False