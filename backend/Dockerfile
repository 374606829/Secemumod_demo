# Stage 1: Build
FROM maven:3.9-eclipse-temurin-17-alpine AS builder
WORKDIR /build

COPY pom.xml .
RUN mvn dependency:go-offline -B

COPY src ./src
RUN mvn package -DskipTests -B

# Stage 2: Run
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

COPY --from=builder /build/target/*.jar app.jar

# Storage volume (seed will write here, mounted at runtime)
RUN mkdir -p /app/storage/mods

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
