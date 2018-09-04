import uuid
import random
import json
from string import ascii_uppercase

GATE_TYPE = "GATE"
KEY_TYPE = "KEY"
BRANCH_TYPE = "BRANCH"

id_alphaindex = 0
id_numindex = 1
key_alphaindex = 0
key_numindex = 1

def gen_id():
    """Generates and returns a unique node ID"""
    global id_alphaindex, id_numindex
    if id_alphaindex >= 26:
        id_alphaindex = 0
        id_numindex += 1

    generated_id  =  ascii_uppercase[id_alphaindex] + str(id_numindex)
    id_alphaindex += 1
    return "ID_" + generated_id

def gen_key_value():
    """Generates a unique key value"""
    global key_alphaindex, key_numindex
    if key_alphaindex >= 26:
        key_alphaindex = 0
        key_numindex += 1

    generated_key = ascii_uppercase[key_alphaindex] + str(key_numindex)
    key_alphaindex += 1
    return "KEY_" + generated_key

class GateNode(object):
    """
    An exploration node representing a locked door or gate. Contains a
    list of requirements that must be met to bypass
    """
    def __init__(self, destination, requirements):
        self.node_id = gen_id()
        self.node_type = GATE_TYPE
        self.destination = destination
        self.requirements = requirements

    def addRequirement(self, requirement):
        self.requirements.append(requirement)

    def addRequirements(self, requirements):
        self.requirements.extend(requirements)

    def reprJson(self):
        return dict(node_type = self.node_type, destination = self.destination, requirements = self.requirements)

class BranchNode(object):
    """
    An exploration node representing a branching path. Connects to multiple
    other nodes via paths
    """
    def __init__(self, paths):
        self.node_id = gen_id()
        self.node_type = BRANCH_TYPE
        self.paths = paths

    def reprJson(self):
        return dict(node_type = self.node_type, paths = self.paths)
    
class KeyNode(object):
    """
    An exploration node representing a key that can be picked up and used to bypass
    GateNodes whose requirements match the key's value
    """
    def __init__(self, key_value):
        self.node_id = gen_id()
        self.node_type = KEY_TYPE
        self.key_value = key_value

    def reprJson(self):
        return dict(node_type = self.node_type, key_value = self.key_value)

    def __repr__(self):
        return str(self.reprJson())

class NodeEncoder(json.JSONEncoder):
    """A JSON encoder for exploration nodes"""
    def default(self, obj):
        if hasattr(obj, 'reprJson'):
            return obj.reprJson()
        else:
            return json.JSONEncoder.default(self, obj)

class TreeConfig(object):
    """
    Object used to keep track of generation progress and configurations throughout
    the recursive generateExplorationTree() method
    """
    def __init__(self, totalNumGatesToGenerate):
        self.totalNumGatesToGenerate = totalNumGatesToGenerate
        self.numGatesRemainingToGenerate = totalNumGatesToGenerate
        self.keysRemainingToPlace = []

    def copyWithoutKeys(self):
        return TreeConfig(self.numGatesRemainingToGenerate)

def generateExplorationTree(destinationTree, treeConfig):
    """
    Recursively generates and returns the root node of an exploration tree in which destinationTree is reachable via at least one
    traversible path if an explorer starts at the returned node

    destinationTree - The sub-tree that will be reachable from the generated tree
    treeConfig - Contains configurations and number of remaining gates and keys to place

    Current limitations
        1. Every gate corresponds to 1 and exactly 1 key - I'd like to support gates that require multiple keys
        2. Every key corresponds to 1 and exactly 1 gate - I'd like to support single-use keys that could fit more than 1 gate 
        3. Doesn't support one-way doors - 
        4. Doesn't support dead ends - This is intentional on purpose. An explorationTree is designed to represent the critical path 
        that must be traversed in order to proceed from origin to destination. 
        5. Doesn't support loops - 
    """    
    if treeConfig.numGatesRemainingToGenerate <= 0:
        # no more gates to generate
        # place the destination tree and any remaining keys off of the current node
        branches = []
        branches.extend(treeConfig.keysRemainingToPlace)
        treeConfig.keysRemainingToPlace = []
        branches.append(destinationTree)
        return generateNodeWithBranches(branches)

    else:
        # keep track of how many branches will extend from the node we're currently generating
        branches = []

        # generate a gate node separating the destination sub-tree from the rest of our tree
        gateNode = GateNode(destinationTree, [])
        keyNode = generateKeyNodeForGate(gateNode)
        branches.append(gateNode)
        treeConfig.numGatesRemainingToGenerate -= 1

        # the key corresponding to our new gate must be placed either up or downstream from the current node
        treeConfig.keysRemainingToPlace.append(keyNode)
        # (maybe) place some keys downstream
        keysToPlace = chooseSomeKeys(treeConfig)

        treeConfig.keysRemainingToPlace = [key for key in treeConfig.keysRemainingToPlace if key not in keysToPlace]

        for key in keysToPlace:
            branches.append(generateExplorationTree(key, treeConfig.copyWithoutKeys()))

        # generate the current node
        currentNode = generateNodeWithBranches(branches)

        # generate the rest of the tree between origin and current node
        return generateExplorationTree(currentNode, treeConfig)

def generateKeyNodeForGate(gateNode):
    """
    Generates a key value, assigns it as a requirement to the input GateNode and returns a KeyNode where the
    corresponding key will be available
    """
    key_value = gen_key_value()
    gateNode.addRequirement(key_value)
    return KeyNode(key_value)

def generateNodeWithBranches(branches):
    """
    Generates and returns an exploration node with the input branches. If only a single
    branch is input, returns this branch instead of creating a new BranchNode
    """
    if len(branches) > 1:
        return BranchNode(branches)
    else:
        return branches[0]

def chooseSomeKeys(treeConfig):
    """ Returns a subset of keys from those remaining to be placed"""
    return [key for key in treeConfig.keysRemainingToPlace if random.choice([True, False])]

exitNode = KeyNode("EXIT")
treeConfig = TreeConfig(3)
explorationTree = generateExplorationTree(exitNode, treeConfig)
print(json.dumps(explorationTree, indent=4, cls=NodeEncoder))
