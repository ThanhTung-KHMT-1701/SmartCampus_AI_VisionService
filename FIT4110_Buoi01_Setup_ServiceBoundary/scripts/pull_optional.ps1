$ErrorActionPreference = "Continue"
$images = @("postgres:15-alpine","rabbitmq:3-management","eclipse-mosquitto:2","traefik:v3.1","swaggerapi/swagger-ui:v5.17.14","prom/prometheus:v2.54.1","grafana/grafana:11.2.0","ultralytics/ultralytics:latest-cpu")
New-Item -ItemType Directory -Force -Path "evidence/buoi-01" | Out-Null
foreach ($img in $images) { docker pull $img }
