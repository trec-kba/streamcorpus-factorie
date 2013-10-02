#!/bin/bash -x

. env.sh

mkdir -p classes

find streamcorpus -name \*.scala -print0 | xargs -0 ${SCALA_HOME}/bin/scalac -d classes

#jar cf ${OUTPUT_JAR} -C classes .
