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
parser.add_argument('-o', default="./pcaps/s1-commands.txt", help='path to the output file')

args = parser.parse_args()
inputfile  = args.i
outputfile = args.o


FEATURE_NAMES = ["iat", "len"]


UNIQUE_CODE = {}
def get_unique_code( fe, lo, hi ):
    key = ",".join([fe, str(lo), str(hi)])
    # whether this tuple is processed
    exist = True
    if key not in UNIQUE_CODE:
        exist = False
        UNIQUE_CODE[key] = (len(UNIQUE_CODE) + 1)
    return (exist, UNIQUE_CODE[key])


# https://github.com/p4lang/behavioral-model?tab=readme-ov-file#using-the-cli-to-populate-tables
#syntax: table_add <table name> <action name> <match fields> => <action parameters> [priority]
def write_entry(f, table_name, action_name, match_fields, action_param):
    f.write("table_add MyIngress.{} {} {} => {}\n".format( table_name, action_name, match_fields, action_param ))

def write_entries(f, domain, classification):
    codes = []
    # for each feature in order
    for i in range(0, len(FEATURE_NAMES)):
        fe = FEATURE_NAMES[i]
        # this feature is not involved in this path
        if fe not in domain:
            continue
        val = domain[ fe ]
        lo = val["min"]
        hi = val["max"]
        
        # we are in a Decision Tree condition (lo, hi], i.e., lo < v <= hi
        #  need to translate to [lo, hi]
        lo = int(lo) + 1
        hi = int(hi) # convert to integer
            
        exist, code = get_unique_code( fe, lo, hi )
        codes.append( str(code) )
        # already exists ==> no need to add a duplicated entry
        if exist:
            continue
        # we are using range table: https://github.com/p4lang/behavioral-model/blob/main/docs/simple_switch.md#range-tables
        #   to match a feature value in a rang of [min, max]
        write_entry(f, "ml_feature_{}".format(fe), "set_code_{}".format(fe),
                     # https://github.com/p4lang/behavioral-model/blob/c74c53661778cc564b7f8e1c1197241319516809/tools/runtime_CLI.py#L638
                     "{}->{}".format(lo, hi), # runtime_CLI separate lo, hi by "->"
                     "{val} {priority}".format( val=code, priority=code) #we use code also as priority
                     )

    # code table
    write_entry(f, "ml_code", "set_result", " ".join(codes), classification)

# minimize the boolean expression which is collected along a path
def minimize( path ):
    # range of possible values of each feature 
    DOMAIN = {
        "iat" : {
            "min": 0, 
            "max": 100*1000000 #100 seconds should be enough
        },
        "len" : {
            "min": 0, 
            "max": 0xFFFF #max size of an IP packet
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
    return domain


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
        # get the class that has the max number of samples
        class_index = a.index(max(a))
        classification = classes[ class_index ]

        # wirte the node information into text file
        write_entries(f, clause, classification)
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



# structure of model: DecisionTreeClassifier
# https://scikit-learn.org/stable/auto_examples/tree/plot_unveil_tree_structure.html#sphx-glr-auto-examples-tree-plot-unveil-tree-structure-py
dt = pd.read_pickle( inputfile )

# output the tree in a text file, write it
features  = [FEATURE_NAMES[i] for i in dt.tree_.feature]

print("write output to", outputfile)
with open(outputfile,"w") as f:
    # visite the tree from the root which has index = 0
    visite(dt, 0, features, f)
