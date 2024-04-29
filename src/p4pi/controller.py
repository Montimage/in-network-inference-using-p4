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
import tempfile

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper
import subprocess


def load_switch_cli(sw, runtime_cli, thrift_address):
    """ This method will start up the CLI and use the contents of the
        command files as input.
    """
    cli = 'simple_switch_CLI'
    # get the port for this particular switch's thrift server
    arr = thrift_address.split(":")
    thrift_port = arr[1] # TODO:
    thrift_ip   = arr[0] 

    print('Configuring switch with file %s' % (runtime_cli))
    with open(runtime_cli, 'r') as fin:
        cli_outfile = 'cli_output.log'
        with open(cli_outfile, 'a') as fout:
            subprocess.Popen([cli, '--thrift-port', thrift_port, '--thrift-ip', thrift_ip],
                             stdin=fin, stdout=fout, stderr=subprocess.STDOUT)

def main(runtime_cli_path, thrift_address, p4_runtime_address, block_class):
    
    try:
        # Create a switch connection object for s1 and s2;
        # this is backed by a P4Runtime gRPC connection.
        # Also, dump all P4Runtime messages sent to switch to given txt files.
        s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address=p4_runtime_address,
            device_id=0,
            proto_dump_file='s1-p4runtime-requests.log')

        # Send master arbitration update message to establish this controller as
        # master (required by P4Runtime before performing any other write operation)
        s1.MasterArbitrationUpdate()
        # Write the rules that performs packet routing
        print("=> load match-action table for routing packets")
        load_switch_cli( s1, "./switch-forward.txt", thrift_address )
        
        # Write the rules that performs inference
        print("=> load match-action table for ML inference")
        load_switch_cli( s1, runtime_cli_path, thrift_address )
        
        print("=> load match-action table for reaction")
        
        block_entry = "table_add MyIngress.reaction drop {} =>".format( block_class )
        f = tempfile.NamedTemporaryFile(mode='w', delete=False)
        f.write( block_entry )
        f.close()

        #load file to the switch
        load_switch_cli( s1, f.name, thrift_address )
        #os.unlink(f.name)
        
    except KeyboardInterrupt:
        print("Bye.")
    except Exception as e:
        print(e)
        raise e

    ShutdownAllSwitchConnections()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')

    parser.add_argument('--runtime-cli', help='The ML model',
                        type=str, action="store", required=False,
                        default='./s1-commands.txt')

    parser.add_argument('--thrift-address', help='Thrift address (in format IP:port) for table updates',
                        type=str, action="store", required=False,
                        default='127.0.0.1:9090')
    parser.add_argument('--p4-runtime-address', help='P4 Runtime RPC server address (in format IP:port)',
                        type=str, action="store", required=False,
                        default='127.0.0.1:50051')

    parser.add_argument('--block-class', help='Traffic class to be blocked (integer)',
                        type=int, action="store", required=True)
    args = parser.parse_args()

    main( args.runtime_cli, args.thrift_address, args.p4_runtime_address, args.block_class)
