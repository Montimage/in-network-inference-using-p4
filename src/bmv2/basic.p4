/* -*- P4_16 -*- */

#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<8>  TYPE_TCP  = 6;
const bit<8>  TYPE_UDP  = 17;

const bit<32> NB_ENTRIES = 2048;

//write and read the first element of a register (which contains an array of elements)
#define FIST_INDEX ((bit<32>)0)
#define WRITE_REG(r, v) r.write(FIST_INDEX, v)
#define READ_REG(r,  v) r.read(v, FIST_INDEX)

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<64> timestamp_t;
typedef bit<8>  inference_result_t; //final classification

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

// tcp header
header tcp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<3>  res;
    bit<3>  ecn;
    bit<6>  ctrl;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

/* UDP header */
header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> udpTotalLen;
    bit<16> checksum;
}

struct metadata {
    //remember this info to avoid accessing from udp or tcp
    bit<16> srcPort;
    bit<16> dstPort;
    //ml features
    timestamp_t iat;

    inference_result_t ml_result;    //final classification result
}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    tcp_t        tcp;
    udp_t        udp;
}

struct digest_t {
    //flow ID is a 5-tuples
    ip4Addr_t srcAddr;  //32 bits
    ip4Addr_t dstAddr;
    bit<16> srcPort;
    bit<16> destPort;
    bit<8> protocol;
    timestamp_t iat;
    bit<16> len;
    inference_result_t class_value; //class of traffic in this flow
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default  : accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            TYPE_TCP: parse_tcp;
            TYPE_UDP: parse_udp;
            default : accept;
        }
    }

    state parse_tcp {
        packet.extract(hdr.tcp);
        //remember src and dst ports to identify this flow
        meta.dstPort = hdr.tcp.dstPort;
        meta.srcPort = hdr.tcp.srcPort;
        transition accept;
    }

    state parse_udp {
        packet.extract(hdr.udp);
        meta.dstPort = hdr.udp.dstPort;
        meta.srcPort = hdr.udp.srcPort;
        transition accept;
    }
}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {   
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    /* default table and its actions for packet forwarding */
    action drop() {
        mark_to_drop(standard_metadata);
    }
    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    /* ml table and its actions for the final result */
    action set_result(inference_result_t val){
        meta.ml_result = val;
    }
    table ml_code{
        key = {
            meta.iat          : range ;
            hdr.ipv4.totalLen : range ;
        }
        actions = {
            NoAction;
            set_result;
        }
       size = 1024;
    }

    //timestamp of the previous packet
    // we need only 1 element for now (without considering IAT of packets belong to a flow)
    register<timestamp_t>(1) last_ts_reg;
    action get_iat(){
        timestamp_t last;
        timestamp_t now;
        READ_REG( last_ts_reg, last );
        //moment the packet arrived at the ingress port
        // bmv2 uses 48 bit to store ingress_global_timestamp
        now = (timestamp_t) standard_metadata.ingress_global_timestamp * 1000;
        //ignore the first packet as there is no IAT 
        if( last != 0 ){
            meta.iat = ( now - last );
        }
        //meta.iat = 93500;
        WRITE_REG( last_ts_reg, now );
    }
    timestamp_t last_ts;

    apply {
        if (hdr.ipv4.isValid() ) {
            //2 steps of inference:
            //  0. extract feature values
            get_iat();
            
            //  1. match the final result
            ml_code.apply();
            
            //log_msg( "iat: {}, len: {} => ({}, {}) => {}", {
            //    meta.iat, hdr.ipv4.totalLen,
            //    meta.ml_code_iat, meta.ml_code_len,
            //    meta.ml_result
            //});
            
            //if( meta.ml_result != 0 )
            {
                // send a digest to controller
                digest<digest_t>(1, {hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, 
                                 meta.srcPort, meta.dstPort,
                                 hdr.ipv4.protocol, 
                                 (bit<64>)meta.iat, hdr.ipv4.totalLen, 
                                 meta.ml_result});
            }
            ipv4_lpm.apply();
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {
         update_checksum(
            hdr.ipv4.isValid(),
            { hdr.ipv4.version,
              hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.tcp);
        packet.emit(hdr.udp);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;
