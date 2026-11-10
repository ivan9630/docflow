#!/bin/sh
set -eu
mkdir -p build
javac --add-modules jdk.httpserver -encoding UTF-8 -d build $(find src/main/java -name '*.java')
java --add-modules jdk.httpserver -cp build fr.ivantchomte.missionflow.App
