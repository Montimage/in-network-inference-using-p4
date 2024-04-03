#!/usr/bin/env python

# Extract features from a pcap file, then write its values to a csv file.
# The pcap file contains packets of a single flow which is sent through switch.
#
# Features:
#  - IAT
#  - IP payload length
#

from scapy.all import *
import argparse, csv, os

def extract_features_from_pcap( inputfile, outputfile, classification ):
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
            if iat < 0:
                print("Ignore unordered packet ", packet )
                continue

            last_ts = ts

            metric = {"iat" : iat, "len": ip_len, "class": classification}
            results.append( metric )
        except AttributeError:
            print("Error while parsing packet", packet)

    if len(results) == 0:
        return

    # need to write CSV header only if the file is not existing
    need_header = not os.path.exists( outputfile )

    # append to output file
    with open( outputfile, 'a', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, results[0].keys() )

        # write the header
        if need_header :
            writer.writeheader()

        # write multiple rows
        writer.writerows( results )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # Add argument
    parser.add_argument('-i', required=True, help='path to pcap file')
    parser.add_argument('-o', required=True, help='path to .csv output file')
    parser.add_argument('-c', required=True, help='classification')
    args = parser.parse_args()

    extract_features_from_pcap( args.i,  args.o, int(args.c) )

