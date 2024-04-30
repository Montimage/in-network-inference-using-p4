/*
 * client.c - A simple connection-based client
 * usage: client <host> <port>
 *
 *
 *  Created on: Sep 21, 2023
 *      Author: nhnghia
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/time.h>

#define NB_ITERATION 10000
#define BUFSIZE 200

/*
 * error - wrapper for perror
 */
void error(char *msg) {
	perror(msg);
	exit(0);
}

/**
 * Number of microseconds per second
 */
#define MICRO 1000000
size_t get_latency(int i, const struct timeval *start){
	struct timeval now;
	gettimeofday( &now, NULL );
	size_t latency = (now.tv_sec * MICRO + now.tv_usec) - (start->tv_sec*MICRO + start->tv_usec);

	printf("%d, %ld.%ld, %ld.%ld, %ld\n", i, start->tv_sec, start->tv_usec, now.tv_sec, now.tv_usec, latency);
	return latency;
}

int main(int argc, char **argv) {
	int socket_fd, port_number, n, i;
	struct sockaddr_in server_addr;
	struct hostent *server;
	char *host_name;
	char buf[BUFSIZE];
	char *iface_name = NULL;
	size_t latencies = 0;
	/* check command line arguments */
	if (argc < 3 || argc > 4) {
		fprintf(stderr, "usage: %s <host_name> <port> <bind-nic>\n", argv[0]);
		exit(0);
	}
	host_name = argv[1];
	port_number = atoi(argv[2]);

	if( argc == 4 )
		iface_name = argv[3];

	/* socket: create the socket */
	socket_fd = socket(AF_INET, SOCK_STREAM, 0);
	if (socket_fd < 0)
		error("ERROR opening socket");

	if( iface_name != NULL ){
		if (setsockopt(socket_fd, SOL_SOCKET, SO_BINDTODEVICE, iface_name, strlen(iface_name)) )
			error("Cannot bind to nic");
	}

	/* gethostbyname: get the server's DNS entry */
	server = gethostbyname(host_name);
	if (server == NULL) {
		fprintf(stderr, "ERROR, no such host as %s\n", host_name);
		exit(0);
	}

	/* build the server's Internet address */
	bzero((char*) &server_addr, sizeof(server_addr));
	server_addr.sin_family = AF_INET;
	bcopy((char*) server->h_addr, (char*) &server_addr.sin_addr.s_addr,
			server->h_length);
	server_addr.sin_port = htons(port_number);

	/* connect: create a connection with the server */
	if (connect(socket_fd, (struct sockaddr*) &server_addr, sizeof(server_addr)) < 0)
		error("ERROR connecting");

	bzero(buf, BUFSIZE);

	//buf must be big enough to contain a timeval
	if( sizeof(struct timeval) >= BUFSIZE ){
		fprintf(stderr, "BUFSIZE must be bigger than %ld", sizeof(struct timeval) );
		exit( 0 );
	}

	printf("index, start time, end time, latency (microsecond)\n");

	for( i=0; i<NB_ITERATION; i++){
		//store the current date into buf
		gettimeofday((struct timeval *) buf, NULL);
		/* write: send the message line to the server */
		n = write(socket_fd, buf, BUFSIZE);
		if (n < 0)
			error("ERROR writing to socket");
		//fflush( socket_fd );

		/* read: print the server's reply */
		bzero(buf, BUFSIZE);
		n = read(socket_fd, buf, BUFSIZE);
		if (n < 0)
			error("ERROR reading from socket");

		latencies += get_latency( i,  (struct timeval *) buf );

		usleep(10000);
	}
	close(socket_fd);
	printf("avg latency: %ld", latencies / NB_ITERATION );
	return 0;
}
