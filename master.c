#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <time.h>
#include "NaiveSocketLibrary/NaiveSocketLibrary.h"

#ifdef _WIN32
    #include <windows.h>
#else
    #include <unistd.h>
#endif

void wait_sec( int seconds )
{
    #ifdef _WIN32
        Sleep( 1000 * seconds );
    #else
        sleep( seconds );
    #endif
}

void broadcast_pos(SOCKET sock, double d, SOCKADDR *peer) {
    sendto(sock, &d, sizeof(d), 0, peer, NSLEndpointV4SocketLen);
}

int main(int argc, char *argv[])
{
    static int so_broadcast = true;
	NSLInit();
    SOCKET sConnection = NSLSocket(AF_INET, SOCK_DGRAM, 0);
    int port;
    double length;
    sscanf(argv[1], "%d", &port);
    sscanf(argv[2], "%lf", &length);
    SOCKADDR *peer = NSLEndpointV4("255.255.255.255", port);
    setsockopt(sConnection, SOL_SOCKET, SO_BROADCAST, &so_broadcast, sizeof so_broadcast);

    double pos = 0;
    broadcast_pos(sConnection, pos, peer);
    puts("here");
    while (1) {
        pos += 1;
        if (pos > length) pos = 0;
        broadcast_pos(sConnection, pos, peer);
        printf("Position: %.9f\n", pos);
        wait_sec(1);
    }

    NSLCloseSocket(sConnection);
    free(peer);
    NSLEnd();
    return 0;
}
