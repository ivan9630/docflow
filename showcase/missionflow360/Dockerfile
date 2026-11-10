FROM eclipse-temurin:21-jdk AS build
WORKDIR /source
COPY src ./src
RUN mkdir build && javac --add-modules jdk.httpserver -d build $(find src/main/java -name '*.java')
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /source/build ./build
COPY web ./web
EXPOSE 8080
CMD ["java","--add-modules","jdk.httpserver","-cp","build","fr.ivantchomte.missionflow.App"]
