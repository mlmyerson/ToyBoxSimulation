class Toy:
    def __init__(self, id, is_target, bin_id):
        self.id = id # unique per toy
        self.target = is_target # is a target toy for a child
        self.home_bin = bin_id # original sorted bin slot
        self.current_bin = bin_id # where the toy lives right now
        self.on_floor = False
        self.target_children = set() # ids of children that want this toy