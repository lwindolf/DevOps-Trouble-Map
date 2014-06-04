SUBDIRS=dotm-frontend dotm-backend dotm-aggregator

# Prepare Python wrapper by inserting path
do_substitution = sed -e 's,[@]pythondir[@],$(pythondir),g'
dotm_python_wrapper: dotm_python_wrapper.in
	$(do_substitution) < dotm_python_wrapper.in > dotm_python_wrapper
	chmod +x dotm_python_wrapper

# Installing python scripts as suggested by
# http://blog.couchbase.com/installing-python-scripts-automake
PYTHON_TOOLS=dotm_backend
${PYTHON_TOOLS}: dotm_python_wrapper
	cp $< $@

BUILT_SOURCES = ${PYTHON_TOOLS}
CLEANFILES= ${PYTHON_TOOLS}
bin_SCRIPTS = ${PYTHON_TOOLS}

