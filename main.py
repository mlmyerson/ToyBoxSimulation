import random

from Bin import Bin
from Child import Child
from Parent import Parent
from Toy import Toy

# Parameters
CHILDREN = 2
PARENTS = 2
MIN_TARGETS = 0
MAX_TARGETS = 3
BINS = 5
TOYS = 100
PRESORT_BINS = True # do all the toys in the bins start maximally sorted?

performance = {}

max__secs = 600 #child loosess interest after 10 mins
search_elapsed_secs = 0
sort_elapsed_secs = 0

# assign each toy an id and bin and whether its a target
def initToys():
    toys = []
    for toy_id in range(TOYS):
        if PRESORT_BINS:
            bin_id = toy_id % BINS
        else:
            bin_id = random.randrange(BINS)
        toy = Toy(toy_id, False, bin_id)
        toys.append(toy)
    return toys

# uniform dist for bin assignment
def initBins(toys):
    bin_lookup = {bin_id: [] for bin_id in range(BINS)}
    for toy in toys:
        bin_lookup[toy.current_bin].append(toy)
    return [Bin(bin_id, bin_lookup[bin_id]) for bin_id in range(BINS)]

# assign each child a set of target toy ids
def initChildren(toys):
    children = []
    toy_pool = list(toys)
    for child_id in range(CHILDREN):
        target_count = random.randint(MIN_TARGETS, MAX_TARGETS)
        if target_count and toy_pool:
            choices = random.sample(toy_pool, min(target_count, len(toy_pool)))
        else:
            choices = []
        target_ids = {toy.id for toy in choices}
        child = Child(child_id, target_ids)
        children.append(child)
        for toy in choices:
            toy.target = True
            toy.target_children.add(child.id)
    return children

def initParents():
    return [Parent(parent_id) for parent_id in range(PARENTS)]


# ! overlap in bins and targets is ok
# ! children may not be looking for a toy at all (MIN_TARGETS=0)
toys = initToys()
pile = [] # toys go in the pile after a bin being emptied
bins = initBins(toys)
children = initChildren(toys)
parents = initParents()

while search_elapsed_secs < max__secs:
    # pick a bin to dump out randomly for each child
		# just pick randomly using uniform dist
    # have the children sort through the toys (0 - ~1 secs per child)
		# a child dumps a bucket
			# ? how many buckets get dumped per run
		# a child sorts through the bucket, taking 0 - ~1 secs per toy
			# a child randomly picks each toy to sort from the pile
				# ! abstract this as a search strategy
				# each toy adds to elapsed time
			# ? how long for a child to find all their toys
	# the run ends if a child finds their toys or all toys have been sorted by kids
		# ? how many bins were tipped over
		# ? how many toys are on the floor
		# ? how many toys did each child find
	continue

while sort_elapsed_secs <= search_elapsed_secs:
	# each parent randomly grabs a toy from the pile
		# sorting strategy:
			# decide to sort 0 - ~1 ratio of the toys
			# sorting each toy takes 0 - ~1 * # of bins secs
				# until ratio of toys is >= target sorted ratio
				# then sorting each toy is 0 - ~1 secs
				# mark toy as sorted
		# ? how many toys were sorted
		# ? how long to sort each toy for target sort number? 
		# ? how long to search all the toys
		# ? how many bins were returned to original state? 
			# ratio as sorted toys / total toys 
	
	
		
	continue