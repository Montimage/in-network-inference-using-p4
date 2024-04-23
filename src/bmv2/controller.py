#!/usr/bin/env python3

# A simple controller which will perform the following actions:
# - configure the switch s1 to perform inference using DecisionTree
# - read continually digests (output from the switch)
#
#
# This controller is based on
#   https://github.com/p4lang/tutorials/blob/d007dc4b95200afd6f9b7055fbc9cc7ff927ef35/exercises/p4runtime/mycontroller.py

import argparse
import os
import json
import re
import sys
from time import sleep
import grpc
import time

inputfile = './tree.txt'
actionfile = './action.txt'

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper
from p4.v1 import p4runtime_pb2, p4runtime_pb2_grpc
import subprocess

CLASS_LABLES = {
   0: "unknown",
   1: "skype",
   2: "whasapp",
   3: "webex"
}

def load_switch_cli(sw, runtime_cli):
    """ This method will start up the CLI and use the contents of the
        command files as input.
    """
    cli = 'simple_switch_CLI'
    # get the port for this particular switch's thrift server
    thrift_port = 9090 # TODO: 

    print('Configuring switch with file %s' % (runtime_cli))
    with open(runtime_cli, 'r') as fin:
        cli_outfile = 'logs/cli_output.log'
        with open(cli_outfile, 'w') as fout:
            subprocess.Popen([cli, '--thrift-port', str(thrift_port)],
                             stdin=fin, stdout=fout)

def buildDigestEntry(p4info_helper, digest_name=None):
    digest_entry = p4runtime_pb2.DigestEntry()
    # using name 
    digest_entry.digest_id = p4info_helper.get_digests_id(digest_name)
    # using id directly
    #digest_entry.digest_id = int(digest_id)
    digest_entry.config.max_timeout_ns = 0
    digest_entry.config.max_list_size = 1
    digest_entry.config.ack_timeout_ns = 0
    return digest_entry

def sendDigestEntry(p4info_helper, sw, digest_name):
    digest_entry = buildDigestEntry(p4info_helper, digest_name=digest_name)
    request = p4runtime_pb2.WriteRequest()
    request.device_id = sw.device_id
    request.election_id.low = 1
    update = request.updates.add()
    update.type = p4runtime_pb2.Update.INSERT
    update.entity.digest_entry.CopyFrom(digest_entry)

    try:
        sw.client_stub.Write(request)
    except grpc.RpcError as e:
        print("Error when requesting digest. A request was probably sent.")

def listMessages(sw):
    request = p4runtime_pb2.StreamMessageRequest()
    sw.requests_stream.put(request)
    for item in sw.stream_msg_resp:
        yield item

def bytes_to_int(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + int(b)
    return result

def bytes_to_ip(ip_bytes):
    result = '.'.join(f'{c}' for c in ip_bytes)
    return result
    
def readDigests(p4info_helper, sw, digest_name):
    for msg in listMessages( sw ):
        if msg.WhichOneof('update')=='digest':
            digest = msg.digest
            #print(digest)
            name = p4info_helper.get_digests_name(digest.digest_id)
            #print ("Digest name", name, digest_name, (name == digest_name))
            # not the interested digest, skip it
            if name != digest_name:
                continue
            #print(digest.data)
            for el in digest.data:
                st = el.struct.members
                # order of elements must be the same as being defined by digest_t in basic.p4
                srcIP   = bytes_to_ip( st[0].bitstring )
                dstIP   = bytes_to_ip( st[1].bitstring )
                srcPort = bytes_to_int( st[2].bitstring )
                dstPort = bytes_to_int( st[3].bitstring )
                proto   = bytes_to_int( st[4].bitstring )
                # feature values
                iat     = bytes_to_int( st[5].bitstring )
                ipLen   = bytes_to_int( st[6].bitstring )
                diffLen = bytes_to_int( st[7].bitstring )
                result  = bytes_to_int( st[8].bitstring )
                # expose the result
                yield( srcIP, dstIP, srcPort, dstPort, proto, iat, ipLen, diffLen, result )


def main(p4info_file_path, bmv2_file_path, runtime_cli_path):
    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    
    # the name of digest which is defined in basic.p4
    DIGEST_NAME = "digest_t"
    try:
        # Create a switch connection object for s1 and s2;
        # this is backed by a P4Runtime gRPC connection.
        # Also, dump all P4Runtime messages sent to switch to given txt files.
        s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0,
            proto_dump_file='logs/s1-p4runtime-requests.log')

        # Send master arbitration update message to establish this controller as
        # master (required by P4Runtime before performing any other write operation)
        s1.MasterArbitrationUpdate()

        # Write the rules that performs inference
        load_switch_cli( s1, runtime_cli_path )

        # send a digest request
        sendDigestEntry(p4info_helper, s1, DIGEST_NAME)
        
        # read classification results from the switch
        with open("logs/predict.csv","w") as predict_file:
            predict_file.write("iat,len,diffLen,class\n") #header
            while True:
                for (srcIP, dstIP, srcPort, dstPort, proto, iat, ipLen, diffLen, result) in readDigests(p4info_helper, s1, DIGEST_NAME):
                    print(srcIP, dstIP, srcPort, dstPort, proto, "=>" , iat, ipLen, diffLen, "=>", CLASS_LABLES[result])
                    predict_file.write("{},{},{},{}\n".format(iat, ipLen, diffLen, result))
            #sleep(0.01)

    except KeyboardInterrupt:
        print("Bye.")
    except Exception as e:
        print(e)

    ShutdownAllSwitchConnections()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='./build/basic.p4.p4info.txt')

    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='./build/basic.json')

    parser.add_argument('--runtime-cli', help='The ML control plane file',
                        type=str, action="store", required=False,
                        default='../offline/pcaps/s1-commands.txt')

    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print("\np4info file not found: %s\nHave you run 'make'?" % args.p4info)
        parser.exit(1)

    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print("\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json)
        parser.exit(1)
   
    main(args.p4info, args.bmv2_json, args.runtime_cli)
