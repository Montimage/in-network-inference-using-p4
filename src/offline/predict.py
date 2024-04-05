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

import pandas as pd
import argparse
from sklearn.tree import DecisionTreeClassifier
import json 

parser = argparse.ArgumentParser()

# Add argument
parser.add_argument('-i', default="./pcaps/dt.model", help='path to the input model')
parser.add_argument('-v', default="[[91000,40]]",     help='X to predict')

args = parser.parse_args()
inputfile  = args.i
X = json.loads( args.v )

CLASS_LABLES = {
   0: "unknown",
   1: "skype",
   2: "whasapp",
   3: "webex"
}

# structure of model: DecisionTreeClassifier
# https://scikit-learn.org/stable/auto_examples/tree/plot_unveil_tree_structure.html#sphx-glr-auto-examples-tree-plot-unveil-tree-structure-py
dt = pd.read_pickle( inputfile )
val = dt.predict( X )[0]
print(CLASS_LABLES[val])
