AC_PREREQ(2.59)
AC_INIT(dotm-node, 0.1, lars.lindner@gmail.com)
AC_CONFIG_SRCDIR([dotm-node.c])

dnl AC_ENABLE_SHARED(yes)
dnl AC_ENABLE_STATIC(no)

#AM_CONFIG_HEADER(config.h)
AM_INIT_AUTOMAKE([0.1 foreign std-options -Wall -Werror])
AM_SILENT_RULES([yes])

# Checks for programs.
AC_PROG_CC
AM_PROG_CC_C_O
AC_PROG_MAKE_SET

# Checks for libraries.

# Checks for header files.
AC_HEADER_STDC
AC_HEADER_SYS_WAIT
AC_CHECK_HEADERS([string.h errno.h signal.h sys/socket.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_C_CONST
AC_TYPE_PID_T

# Checks for library functions.
AC_FUNC_FORK
AC_FUNC_MALLOC
AC_FUNC_REALLOC
AC_CHECK_FUNCS([memset strdup strpbrk strstr])
AC_OUTPUT

pkg_modules="	glib-2.0
		libevent"
PKG_CHECK_MODULES(PACKAGE, [$pkg_modules])

AC_CONFIG_FILES([
Makefile
])
AC_OUTPUT
