class Bin:
    def __init__(self, id, toys):
        self.id = id # id of bin
        self.toys = toys # toys in bin
        self.sorted_toys = self.findSortedToys()
        self.is_empty = self.isEmpty()
    
        # check the number of sorted toys in each bin
    def findSortedToys(self):
        sorted_toys = [toy for toy in self.toys if not toy.on_floor and toy.current_bin == self.id]
        return len(sorted_toys)

        # check how many toys are in the bin
    def isEmpty(self):
        return len(self.toys) == 0