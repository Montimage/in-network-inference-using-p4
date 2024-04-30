/*
 * echoserver.c - A simple connection-based echo server
 * usage: echoserver <port>
 *
 *  Created on: Sep 21, 2023
 *      Author: nhnghia
 */

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <netdb.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define BUFSIZE 1500

#if 0
/*
 * Structs exported from netinet/in.h (for easy reference)
 */

/* Internet address */
struct in_addr {
	unsigned int s_addr;
};

/* Internet style socket address */
struct sockaddr_in  {
	unsigned short int sin_family; /* Address family */
	unsigned short int sin_port;   /* Port number */
	struct in_addr sin_addr;	 /* IP address */
	unsigned char sin_zero[...];   /* Pad to size of 'struct sockaddr' */
};

/*
 * Struct exported from netdb.h
 */

/* Domain name service (DNS) host entry */
struct hostent {
	char    *h_name;        /* official name of host */
	char    **h_aliases;    /* alias list */
	int     h_addrtype;     /* host address type */
	int     h_length;       /* length of address */
	char    **h_addr_list;  /* list of addresses */
}
#endif

/*
 * error - wrapper for perror
 */
void error(char *msg) {
	perror(msg);
	exit(1);
}

int main(int argc, char **argv) {
	int server_fd; /* listening socket */
	int client_fd; /* connection socket */
	int server_port; /* port to listen on */
	unsigned int client_len; /* byte size of client's address */
	struct sockaddr_in server_addr; /* server's addr */
	struct sockaddr_in client_addr; /* client addr */
	char buf[BUFSIZE]; /* message buffer */
	int optval; /* flag value for setsockopt */
	int n; /* message byte size */
	char client_ip[INET_ADDRSTRLEN + 1];
	int client_port;

	/* check command line args */
	if (argc != 2) {
		fprintf(stderr, "usage: %s <port>\n", argv[0]);
		exit(1);
	}
	server_port = atoi(argv[1]);

	/* socket: create a socket */
	server_fd = socket(AF_INET, SOCK_STREAM, 0);
	if (server_fd < 0)
		error("ERROR opening socket");

	/* setsockopt: Handy debugging trick that lets
	 * us rerun the server immediately after we kill it;
	 * otherwise we have to wait about 20 secs.
	 * Eliminates "ERROR on binding: Address already in use" error.
	 */
	optval = 1;
	setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, (const void*) &optval,
			sizeof(int));

	/* build the server's internet address */
	bzero((char*) &server_addr, sizeof(server_addr));
	server_addr.sin_family = AF_INET; /* we are using the Internet */
	server_addr.sin_addr.s_addr = htonl(INADDR_ANY); /* accept reqs to any IP addr */
	server_addr.sin_port = htons((unsigned short) server_port); /* port to listen on */

	/* bind: associate the listening socket with a port */
	if (bind(server_fd, (struct sockaddr*) &server_addr, sizeof(server_addr)) < 0)
		error("ERROR on binding");

	/* listen: make it a listening socket ready to accept connection requests */
	if (listen(server_fd, 5) < 0) /* allow 5 requests to queue up */
		error("ERROR on listen");

	/* main loop: wait for a connection request, echo input line,
	 then close connection. */
	client_len = sizeof(client_addr);
	while( 1 ){

		/* accept: wait for a connection request */
		client_fd = accept(server_fd, (struct sockaddr*) &client_addr, &client_len);
		if (client_fd < 0)
			error("ERROR on accept");

		//Resolving Client Address
		bzero( client_ip, sizeof( client_ip) );
		inet_ntop(AF_INET, &client_addr.sin_addr, client_ip, INET_ADDRSTRLEN);
		client_port = ntohs(client_addr.sin_port);
		printf("Got connection from %s:%d -- client fd: %d\n", client_ip, client_port, client_fd);

		//loop until client disconnected?
		while( 1 ){
			/* read: read input string from the client */
			n = read(client_fd, buf, BUFSIZE);

			if (n < 0){
				perror("ERROR reading from socket");
				break;
			} else if( n == 0 ){
				//no more data
				break;
			}
			/* write: echo the input string back to the client */
			n = write(client_fd, buf, n);
			if (n <= 0){
				error("ERROR writing to socket");
				break;
			}
		}
		close(client_fd);
	}
}
