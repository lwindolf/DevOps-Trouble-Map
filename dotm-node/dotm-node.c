/* daemonize() from gtk-transmission daemon (GPLv2 or 3) 
   Copyright (C) 2008-2014 Mnemosyne LLC
*/

#include <string.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#ifndef _WIN32
#include <netinet/in.h>
# ifdef _XOPEN_SOURCE_EXTENDED
#  include <arpa/inet.h>
# endif
#include <sys/socket.h>
#endif
#include <fcntl.h> /* open */
#include <unistd.h> /* daemon */
#include <glib.h>
#include <locale.h>

#include <event2/bufferevent.h>
#include <event2/buffer.h>
#include <event2/listener.h>
#include <event2/util.h>
#include <event2/event.h>

#define debug 0

static const int PORT = 4848;

static void listener_cb(struct evconnlistener *, evutil_socket_t,
    struct sockaddr *, int socklen, void *);
static void conn_writecb(struct bufferevent *, void *);
static void conn_eventcb(struct bufferevent *, short, void *);
static void signal_cb(evutil_socket_t, short, void *);

#if defined (WIN32)
 #define USE_NO_DAEMON
#elif !defined (HAVE_DAEMON) || defined (__UCLIBC__)
 #define USE_TR_DAEMON
#else
 #define USE_OS_DAEMON
#endif

static int
daemonize (int nochdir, int noclose)
{
#if defined (USE_OS_DAEMON)

    return daemon (nochdir, noclose);

#elif defined (USE_TR_DAEMON)

    /* this is loosely based off of glibc's daemon () implementation
     * http://sourceware.org/git/?p=glibc.git;a=blob_plain;f=misc/daemon.c */

    switch (fork ()) {
        case -1: return -1;
        case 0: break;
        default: _exit (0);
    }

    if (setsid () == -1)
        return -1;

    if (!nochdir)
        if (chdir ("/"))
		perror ("chdir");

    if (!noclose) {
        int fd = open ("/dev/null", O_RDWR, 0);
        dup2 (fd, STDIN_FILENO);
        dup2 (fd, STDOUT_FILENO);
        dup2 (fd, STDERR_FILENO);
        close (fd);
    }

    return 0;

#else /* USE_NO_DAEMON */
    return 0;
#endif
}

int
main(int argc, char **argv)
{
	struct event_base *base;
	struct evconnlistener *listener;
	struct event *signal_event;

	struct sockaddr_in sin;
#ifdef _WIN32
	WSADATA wsa_data;
	WSAStartup(0x0201, &wsa_data);
#endif

	setlocale(LC_ALL, "C");

	if (daemon (1, 0) < 0) {
		fprintf (stderr, "Failed to daemonize: %s", strerror (errno));
		exit (1);
	}

	base = event_base_new();
	if (!base) {
		fprintf(stderr, "Could not initialize libevent!\n");
		return 1;
	}

	memset(&sin, 0, sizeof(sin));
	sin.sin_family = AF_INET;
	sin.sin_port = htons(PORT);

	listener = evconnlistener_new_bind(base, listener_cb, (void *)base,
	    LEV_OPT_REUSEABLE|LEV_OPT_CLOSE_ON_FREE, -1,
	    (struct sockaddr*)&sin,
	    sizeof(sin));

	if (!listener) {
		fprintf(stderr, "Could not create a listener!\n");
		return 1;
	}

	signal_event = evsignal_new(base, SIGINT, signal_cb, (void *)base);

	if (!signal_event || event_add(signal_event, NULL)<0) {
		fprintf(stderr, "Could not create/add a signal event!\n");
		return 1;
	}

	event_base_dispatch(base);

	evconnlistener_free(listener);
	event_free(signal_event);
	event_base_free(base);

	return 0;
}

#define NETSTAT_COMMAND "/bin/netstat -an"
#define NETSTAT_ERROR_MSG "Error when calling netstat!"

#define IPADDR_COMMAND "/sbin/ip addr"
#define IPADDR_ERROR_MSG "Error when calling ip addr!"

#define HOSTNAME_LINE "hostname="

#define NEW_LINE "\n"

static void
listener_cb(struct evconnlistener *listener, evutil_socket_t fd,
    struct sockaddr *sa, int socklen, void *user_data)
{
	struct event_base *base = user_data;
	struct bufferevent *bev;
	GError* err = NULL;
	gchar *output = NULL, *errout = NULL;
	gint status = 99;

	bev = bufferevent_socket_new(base, fd, BEV_OPT_CLOSE_ON_FREE);
	if (!bev) {
		fprintf(stderr, "Error constructing bufferevent!");
		event_base_loopbreak(base);
		return;
	}
	bufferevent_setcb(bev, NULL, conn_writecb, conn_eventcb, NULL);
	bufferevent_enable(bev, EV_WRITE);
	bufferevent_disable(bev, EV_READ);
	setlocale(LC_ALL, "C");

	/* First give hostname */
	bufferevent_write (bev, HOSTNAME_LINE, strlen (HOSTNAME_LINE));
	bufferevent_write (bev, g_get_host_name (), strlen (g_get_host_name ()));

	bufferevent_write (bev, NEW_LINE, strlen (NEW_LINE));

	// FIXME: prefix output to allow exact matching!

	// FIXME: according to glib manual G_SPAN_SEARCH_PATH security issue
	// so g_spawn_sync needs to be used instead!
	if (!g_spawn_command_line_sync (NETSTAT_COMMAND, &output, &errout, &status, &err)) {
		fprintf (stderr, "Failed to run '%s': %s\n", NETSTAT_COMMAND, err->message);
		g_error_free (err);
	}

	if (output)
		bufferevent_write(bev, output, strlen(output));
	else
		bufferevent_write(bev, NETSTAT_ERROR_MSG, strlen(NETSTAT_ERROR_MSG));

	g_free (output);
	g_free (errout);
	output = NULL;
	errout = NULL;

	bufferevent_write (bev, NEW_LINE, strlen (NEW_LINE));

	if (!g_spawn_command_line_sync (IPADDR_COMMAND, &output, &errout, &status, &err)) {
		fprintf (stderr, "Failed to run '%s': %s\n", IPADDR_COMMAND, err->message);
		g_error_free (err);
	}

	if (output)
		bufferevent_write(bev, output, strlen(output));
	else
		bufferevent_write(bev, IPADDR_ERROR_MSG, strlen(IPADDR_ERROR_MSG));

	g_free (output);
	g_free (errout);
}

static void
conn_writecb(struct bufferevent *bev, void *user_data)
{
	struct evbuffer *output = bufferevent_get_output(bev);
	if (evbuffer_get_length(output) == 0) {
		bufferevent_free(bev);
	}
}

static void
conn_eventcb(struct bufferevent *bev, short events, void *user_data)
{
	if (debug & events & BEV_EVENT_ERROR) {
		printf("Got an error on the connection: %s\n",
		    strerror(errno));/*XXX win32*/
	}
	/* None of the other events can happen here, since we haven't enabled
	 * timeouts */
	bufferevent_free(bev);
}

static void
signal_cb(evutil_socket_t sig, short events, void *user_data)
{
	struct event_base *base = user_data;
	struct timeval delay = { 2, 0 };

	event_base_loopexit(base, &delay);
}

