class Bin:
    def __init__(self, id, toys):
        self.toys = toys
        self.sorted_toys = self.findSortedToys()
        self.id = id # id of bin
    
        # check the number of sorted toys in each bin
    def findSortedToys(self):
        pass