#!/bin/bash -x
# Utility script for running factorie language analyzer on a streamcorpus chunk file.
#
# usage:
#  ./factorie.sh input_streamcorpus.sc output_streamcorpus.sc

. env.sh

export CLASSPATH=${CLASSPATH}:classes

# normal
exec /usr/bin/time ${SCALA_HOME}/bin/scala -J-Xmx5G streamcorpus.factorie.Annotate1 "$@"

# ye olde java prof
#exec /usr/bin/time ${SCALA_HOME}/bin/scala -J-Xmx5G -J-Xprof streamcorpus.factorie.Annotate1 "$@"

# hprof (very slow)
#exec /usr/bin/time ${SCALA_HOME}/bin/scala -J-Xmx5G -J-agentlib:hprof=cpu=times streamcorpus.factorie.Annotate1 "$@"

# enable JMX debugging
#exec /usr/bin/time ${SCALA_HOME}/bin/scala -J-Xmx5G \
#-J-Dcom.sun.management.jmxremote.port=6969 \
#-J-Dcom.sun.management.jmxremote.authenticate=false \
#-J-Dcom.sun.management.jmxremote.ssl=false \
#streamcorpus.factorie.Annotate1 "$@"
