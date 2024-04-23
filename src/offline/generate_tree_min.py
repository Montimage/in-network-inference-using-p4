#!/usr/bin/env python3

# Expand a DecisionTreeClassifier to a text file which is structured as following:
# - for each feature:
#    + feature-i: list of thresholds 
#    + ...
# - for each path from root to leaf:
#    + IF condition-1 and condition-2 and ... THEN classification-1
#
#
# See an example in pcaps/tree_min.txt

import numpy as np
import pandas as pd
import argparse
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from sklearn.tree import export_graphviz
import pydotplus



parser = argparse.ArgumentParser()

# Add argument
parser.add_argument('-i', default="./pcaps/dt.model", help='path to the input model')
parser.add_argument('-o', default="./pcaps/tree_min.txt", help='path to the output file')

args = parser.parse_args()
inputfile  = args.i
outputfile = args.o

# minimize the boolean expression which is collected along a path
def minimize( path ):
    # range of possible values of each feature 
    DOMAIN = {
        "iat" : {
            "min": 0, 
            "max": 100*1000*1000000 #100 seconds should be enough
        },
        "len" : {
            "min": 0, 
            "max": 0xFFFF #max size of an IP packet
        },
        "diffLen" : {
            "min": 0, 
            "max": 2*0xFFFF #2 times of packet size
        }
    }

    domain = {}
    for (feature, sign, threshold) in path:
        if feature not in DOMAIN:
            raise Exception("need to set in DOMAIN min and max of", feature)
            
        # init
        if feature not in domain:
            domain[feature] = DOMAIN[feature].copy()

        val = domain[ feature ]
        
        if sign == "<=":
            # as we have condition (feature <= threshold)
            #   then we reduce its upper bound (max)
            val["max"] = threshold
        else:
            # here we have condition (feature > threshold)
            #   then we increase its lower bound (min)
            val["min"] = threshold

    new_path = []
    for fe in domain:
        val = domain[ fe ]
        VAL = DOMAIN[ fe ]

        if val["min"] > val["max"]:
            print("impossible")
            continue

        if val["min"] != VAL["min"]:
            # lower bound was updated
            new_path.append( str(val["min"]) + "<" + fe )

        if val["max"] != VAL["max"]:
            # upper bound was updated
            new_path.append( "" + fe + "<=" + str(val["max"]) )

    return new_path


# Visite the tree using Depth-first search
def visite(dt, node_id, features, file, path = [] ):
    classes = dt.classes_
    tree  = dt.tree_
    left  = tree.children_left
    right = tree.children_right

    # do we reach a leaf node?
    is_leaf = (left[ node_id ] == right[ node_id ])

    if is_leaf:
        # print path from root to this leaf node
        new_path = []
        for (n_id, sign) in path:
            threshold = tree.threshold[n_id]
            feature   = features[n_id]
            new_path.append( (feature, sign, threshold) )

        clause = minimize( new_path )

        # see https://scikit-learn.org/stable/auto_examples/tree/plot_unveil_tree_structure.html#what-is-the-values-array-used-here
        a = list(tree.value[node_id][0])
        class_index = a.index(max(a))
        classification = classes[ class_index ]

        # wirte the node information into text file
        file.write("\t IF {0} THEN {1};\n".format( " and ".join(clause), str(classification) ))
        return
    else:
        # need to clone the path to avoid being add nodes in the left branch
        org_path = path.copy()
        # visit the left branch first
        path.append( (node_id, "<=") )
        visite( dt, left[ node_id ], features, file, path )

        # visite the right branch
        org_path.append( (node_id, ">") )
        visite( dt, right[ node_id ], features, file, org_path )



FEATURE_NAMES = ["iat", "len", "diffLen"]

# structure of model: DecisionTreeClassifier
# https://scikit-learn.org/stable/auto_examples/tree/plot_unveil_tree_structure.html#sphx-glr-auto-examples-tree-plot-unveil-tree-structure-py
dt = pd.read_pickle( inputfile )

# output the tree in a text file, write it
threshold = dt.tree_.threshold
features  = [FEATURE_NAMES[i] for i in dt.tree_.feature]

data = {}

for i, fe in enumerate(features):
    if not fe in data:
        data[fe] = []

    if threshold[i] != -2.0:
        data[fe].append( int(threshold[i]) )

print("write output to", outputfile)
with open(outputfile,"w") as f:
    for fe in data:
        val = data[fe]
        val.sort()
        f.write("{0} = {1};\n".format( fe, str(val) ))
    
    # visite the tree from the root which has index = 0
    visite(dt, 0, features, f)
