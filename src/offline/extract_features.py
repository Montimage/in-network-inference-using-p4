#!/usr/bin/env python

# Extract features from a pcap file, then write its values to a csv file.
# The pcap file contains packets of a single flow which is sent through switch.
#
# Features:
#  - IAT
#  - IP payload length
#

from scapy.all import *
import argparse, csv

parser = argparse.ArgumentParser()

# Add argument
parser.add_argument('-i', required=True, help='path to pcap file')
parser.add_argument('-o', required=True, help='path to .csv output file')
parser.add_argument('-c', required=True, help='classification')
args = parser.parse_args()

# parameters
inputfile      = args.i
outputfile     = args.o
classification = int(args.c)

results = []
last_ts = 0

#read the pcap file and extract the features for each packet
all_packets = rdpcap(inputfile)

# for each packet in the pcap file
for packet in all_packets:
    try:
        ts     = packet.time # e.g., 1712073023.619379
        ip_len = packet.len  # e.g., 76

        ts = int( ts * 1000000) # in microsecond

        # for the first time
        if last_ts == 0:
            last_ts = ts
            continue

        # get IAT - Inter Arrival Time
        iat = ts - last_ts
        last_ts = ts

        metric = [ iat, ip_len, classification ]
        results.append( metric )
    except AttributeError:
        print("Error while parsing packet", packet)

with open( outputfile, 'w', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)

    # write the header
    writer.writerow(["iat", "len", "classification"])

    # write multiple rows
    writer.writerows( results )
