#!/usr/bin/env python3

# Valid X again a DecisionTreeClassifier.
# and explain its decision paths

import pandas as pd
import argparse
from sklearn.tree import DecisionTreeClassifier
import json 

parser = argparse.ArgumentParser()

# Add argument
parser.add_argument('-i', default="./pcaps/dt.model", help='path to the input model')
parser.add_argument('-v', default="[[93500,46],[93501,64]]", help='X to predict')

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
feature = dt.tree_.feature
threshold = dt.tree_.threshold

val = dt.predict( X )
print("Prediction:", [CLASS_LABLES[i] for i in val])

# https://scikit-learn.org/stable/auto_examples/tree/plot_unveil_tree_structure.html#decision-path

#print(dt.decision_path(X))
node_indicator = dt.decision_path(X)
leaf_id = dt.apply(X)

for sample_id in range(0, len(X)):
    # obtain ids of the nodes `sample_id` goes through, i.e., row `sample_id`
    node_index = node_indicator.indices[
        node_indicator.indptr[sample_id] : node_indicator.indptr[sample_id + 1]
    ]
    
    print("Rules used to predict sample {id}: {pred}".format(id=sample_id, pred=CLASS_LABLES[val[sample_id]]))
    for node_id in node_index:
        # continue to the next node if it is a leaf node
        if leaf_id[sample_id] == node_id:
            continue
    
        # check if value of the split feature for sample 0 is below threshold
        if X[sample_id][feature[node_id]] <= threshold[node_id]:
            threshold_sign = "<="
        else:
            threshold_sign = ">"
    
        print(
            " - decision node {node} : (X[{sample}, {feature}] = {value}) "
            "{inequality} {threshold})".format(
                node=node_id,
                sample=sample_id,
                feature=feature[node_id],
                value=X[sample_id][feature[node_id]],
                inequality=threshold_sign,
                threshold=threshold[node_id],
            )
    )