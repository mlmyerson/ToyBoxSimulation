class Child:
    def __init__(self, id, targets):
        self.id = id # unique id of child
        self.targets = set(targets) # toy ids this child is searching for
        self.time_elapsed_secs = 0.0 # how many secs spend searching for targets