#!/usr/bin/env python3

# Extract features from the pcap files in this folder
#

import sys, os, glob, json
import extract_features as ef

# extract "skype" from "./skype.v1.pcap"
def get_class_name( file_name ):
    base_name = os.path.basename( file_name )
    class_name = base_name.split(".")[0]
    return class_name


# directory containing this script
__DIR__ = os.path.dirname(os.path.realpath(__file__))
DIR     = os.path.join(__DIR__, "pcaps")

OUTPUT_FILE = os.path.join(DIR, "features.csv")

class_index = 0
file_names = {}

# for each pcap files
for file_name in glob.glob('{0}/*.pcap'.format(DIR), recursive=True):
    class_name = get_class_name( file_name )

    # remember index of this class_name
    if not class_name in file_names:
        class_index += 1
        file_names[ class_name ] = class_index

    print("{0}. processing {1}".format( class_index, file_name ))
    ef.extract_features_from_pcap( file_name, OUTPUT_FILE, class_index )

# write map class-index
with open(os.path.join(DIR, "map.json"), "w") as outfile:
    json.dump( file_names, outfile, indent=3, sort_keys=False)