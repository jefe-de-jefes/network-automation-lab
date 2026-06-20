#!/bin/bash
ulimit -n 1024
/usr/sbin/sshd
exec /sbin/tini -- /usr/lib/frr/docker-start
