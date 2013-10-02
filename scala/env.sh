SCALA_HOME=${HOME}/psrc/scala/scala-2.10.2

NCLASSPATH=`echo lib/*.jar | tr ' ' ':'`
NCLASSPATH=${NCLASSPATH}:${HOME}/factorie_classes
if [ -z ${CLASSPATH} ]; then
	CLASSPATH=${NCLASSPATH}
else
	CLASSPATH=${CLASSPATH}:${NCLASSPATH}
fi
export CLASSPATH

