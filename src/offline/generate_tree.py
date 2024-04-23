#!/usr/bin/env python3

# Expand a DecisionTreeClassifier to a text file which is structured as following:
# - for each feature:
#    + feature-i: list of thresholds 
#    + ...
# - for each path from root to leaf:
#    + IF condition-1 and condition-2 and ... THEN classification-1
#
#
# See an example in pcaps/tree.txt

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
parser.add_argument('-o', default="./pcaps/tree.txt", help='path to the output file')

args = parser.parse_args()
inputfile  = args.i
outputfile = args.o


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
        clause = []
        for (n_id, sign) in path:
            threshold = tree.threshold[n_id]
            feature   = features[n_id]
            clause.append("" + feature + sign + str(threshold))

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
