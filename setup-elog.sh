export ELOG_DIR=$(which elog | sed 's^/bin/^/lib/^g')

if [ "$(domainname)" != "mlab" ]; then
    # on pippin (dev laptop) use local databae
    export ELOG_HOST=localhost ELOG_USER=root ELOG_PASSWD=""
fi
