
import numpy as np
import pandas as pd
import argparse
from sklearn.metrics import accuracy_score
from sklearn import tree
import pickle


parser = argparse.ArgumentParser()

# Add argument
parser.add_argument('-i', default="./pcaps/features.csv", help='path to csv. dataset')
parser.add_argument('-o', default="./pcaps/dt.model", help='path to output model file')
args = parser.parse_args()

# extract argument
inputfile  = args.i
outputfile = args.o

# Training set X and Y
csv  = pd.read_csv(inputfile)
data = csv.values.tolist()
X = [i[0:-1] for i in data] #the columns before the last one are features
Y = [i[-1]   for i in data] #last column is "classification"

#print(X[0], Y[0])
#print(X[-1], Y[-1])

# prepare training and testing set
X = np.array(X)
Y = np.array(Y)

# print(X)

# decision tree: https://scikit-learn.org/stable/modules/tree.html#tree
dt = tree.DecisionTreeClassifier()
dt.fit(X, Y)

# visualize the tree
#tree.plot_tree( dt )
#Predict_Y = dt.predict(X)
#print(accuracy_score(Y, Predict_Y))

# dump model to f
print("write model to", outputfile)
pickle.dump(dt, open(outputfile, 'wb'))