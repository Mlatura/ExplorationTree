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

    def repr_json(self):
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

    def repr_json(self):
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

    def repr_json(self):
        return dict(node_type = self.node_type, key_value = self.key_value)

    def __repr__(self):
        return str(self.reprJson())

class NodeEncoder(json.JSONEncoder):
    """A JSON encoder for exploration nodes"""

    def default(self, obj):
        if hasattr(obj, 'repr_json'):
            return obj.repr_json()
        else:
            return json.JSONEncoder.default(self, obj)

class TreeConfig(object):
    """
    Object used to keep track of generation progress and configurations throughout
    the recursive generate_exploration_tree() method
    """

    def __init__(self, total_num_gates_to_generate):
        self.total_num_gates_to_generate = total_num_gates_to_generate
        self.num_gates_remaining_to_generate = total_num_gates_to_generate
        self.keys_remaining_to_place = []

    def copy_without_keys(self):
        """ Returns a copy of this TreeConfig with no keysRemainingToPlace """

        return TreeConfig(self.num_gates_remaining_to_generate)

def generate_exploration_tree(destination_tree, tree_config):
    """
    Recursively generates and returns the root node of an exploration tree in which destination_tree is reachable via at least one
    traversible path if an explorer starts at the returned node

    destination_tree - The sub-tree that will be reachable from the generated tree
    tree_config - Contains configurations and number of remaining gates and keys to place

    Current limitations
        1. Every gate corresponds to 1 and exactly 1 key - I'd like to support gates that require multiple keys
        2. Every key corresponds to 1 and exactly 1 gate - I'd like to support single-use keys that could fit more than 1 gate 
        3. Doesn't support one-way doors - 
        4. Doesn't support dead ends - This is intentional on purpose. An explorationTree is designed to represent the critical path 
        that must be traversed in order to proceed from origin to destination. 
        5. Doesn't support loops - 
        6. Will never generate a sub-tree containing multiple keys that are required outside of that sub-tree
    """    

    if tree_config.num_gates_remaining_to_generate <= 0:
        # no more gates to generate
        # place the destination tree and any remaining keys off of the current node
        branches = []
        branches.extend(tree_config.keys_remaining_to_place)
        tree_config.keys_remaining_to_place = []
        branches.append(destination_tree)
        return generate_node_with_branches(branches)

    else:
        # keep track of how many branches will extend from the node we're currently generating
        branches = []

        # generate a gate node separating the destination sub-tree from the rest of our tree
        gate_node = GateNode(destination_tree, [])
        key_node = generate_key_node_for_gate(gate_node)
        branches.append(gate_node)
        tree_config.num_gates_remaining_to_generate -= 1

        # the key corresponding to our new gate must be placed either up or downstream from the current node
        tree_config.keys_remaining_to_place.append(key_node)

        # (maybe) place some keys downstream
        keys_to_place = choose_some_keys(tree_config)
        tree_config.keys_remaining_to_place = [key for key in tree_config.keys_remaining_to_place if key not in keys_to_place]
        for key in keys_to_place:
            branches.append(generate_exploration_tree(key, tree_config.copy_without_keys()))

        # generate the current node
        current_node = generate_node_with_branches(branches)

        # generate the rest of the tree between origin and current node
        return generate_exploration_tree(current_node, tree_config)

def generate_key_node_for_gate(gate_node):
    """
    Generates a key value, assigns it as a requirement to the input GateNode and returns a KeyNode where the
    corresponding key will be available
    """

    key_value = gen_key_value()
    gate_node.addRequirement(key_value)
    return KeyNode(key_value)

def generate_node_with_branches(branches):
    """
    Generates and returns an exploration node with the input branches. If only a single
    branch is input, returns this branch instead of creating a new BranchNode
    """

    if len(branches) > 1:
        return BranchNode(branches)
    else:
        return branches[0]

def choose_some_keys(tree_config):
    """ Returns a subset of keys from those remaining to be placed"""

    return [key for key in tree_config.keys_remaining_to_place if random.choice([True, False])]

exit_node = KeyNode("EXIT")
tree_config = TreeConfig(3)
exploration_tree = generate_exploration_tree(exit_node, tree_config)
print(json.dumps(exploration_tree, indent=4, cls=NodeEncoder))
