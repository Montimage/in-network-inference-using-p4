#!/usr/bin/env python3

# Valid a csv file againt a decision tree model
# The csv file is structured identically as the one being used to train the model, e.g.,:
#  - the first n columns contain features (X)
#  - the last column contain classification (Y)

import numpy as np
import pandas as pd
import argparse
from sklearn.tree import DecisionTreeClassifier

parser = argparse.ArgumentParser()

# Add argument
parser.add_argument('-i', default="./pcaps/dt.model", help='path to the input model')
parser.add_argument('-v', default="../bmv2/logs/predict.csv", help='path to csv file to validate')

args = parser.parse_args()
inputfile  = args.i
testfile   = args.v

# structure of model: DecisionTreeClassifier
# https://scikit-learn.org/stable/auto_examples/tree/plot_unveil_tree_structure.html#sphx-glr-auto-examples-tree-plot-unveil-tree-structure-py
dt = pd.read_pickle( inputfile )

# Training set X and Y
csv  = pd.read_csv( testfile )
data = csv.values.tolist()
X = [i[0:-1] for i in data] #the columns before the last one are features
Y = [i[-1]   for i in data] #last column is "classification"

#print(X[0], Y[0])
#print(X[-1], Y[-1])

# prepare testing set
X = np.array(X)
Y = np.array(Y)

# see https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html#sklearn.tree.DecisionTreeClassifier.score
# print the mean accuracy on the given test data (X) and labels (Y).
print("Score", dt.score(X,Y))