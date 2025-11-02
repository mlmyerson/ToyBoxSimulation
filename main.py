import json
import random
from pathlib import Path

from Bin import Bin
from Child import Child
from Parent import Parent
from Toy import Toy

SETTINGS_PATH = Path(__file__).with_name("settings.json")

DEFAULT_SETTINGS = {
    "children": 2,
    "parents": 2,
    "min_targets": 0,
    "max_targets": 3,
    "bins": 5,
    "toys": 100,
    "presort_bins": True,
    "max_search_seconds": 600,
    "random_seed": None,
}


def load_settings(path: Path = SETTINGS_PATH):
    settings = DEFAULT_SETTINGS.copy()
    if path.exists():
        with path.open() as handle:
            file_settings = json.load(handle)
        settings.update(file_settings)
    return settings


settings = load_settings()

if settings.get("random_seed") is not None:
    random.seed(settings["random_seed"])

CHILDREN = settings["children"]
PARENTS = settings["parents"]
MIN_TARGETS = settings["min_targets"]
MAX_TARGETS = settings["max_targets"]
BINS = settings["bins"]
TOYS = settings["toys"]
PRESORT_BINS = settings["presort_bins"]
MAX_SEARCH_SECONDS = settings["max_search_seconds"]

performance = {}

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

while search_elapsed_secs < MAX_SEARCH_SECONDS:
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