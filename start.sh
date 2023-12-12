echo "building application_api"

cd ./application_api &&
docker build -t application_api:latest . &&
cd .. &&

echo "building routing_api"

cd ./routing_api &&
docker build -t routing_api:latest . &&
cd .. &&

echo "building performance_stats"

cd ./performance_stats &&
docker build -t performance_stats:latest . &&

cd ..
docker-compose up -d
