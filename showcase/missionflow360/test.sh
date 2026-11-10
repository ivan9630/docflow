#!/bin/sh
set -eu
mkdir -p build
javac --add-modules jdk.httpserver -encoding UTF-8 -d build $(find src/main/java src/test/java -name '*.java')
java -ea -cp build fr.ivantchomte.missionflow.WorkflowTest
