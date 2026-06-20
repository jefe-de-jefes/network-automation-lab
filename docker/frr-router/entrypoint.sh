#!/bin/bash
ulimit -n 1024
exec /sbin/tini -- /usr/lib/frr/docker-start
