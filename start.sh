echo "running tests"
python3 -m unittest routing_api.tests.test_routing_api

echo "building application_api"

cd ./application_api &&
docker build -t application_api:latest . &&
cd .. &&

echo "building routing_api"

cd ./routing_api &&
docker build -t routing_api:latest . &&
cd .. &&

docker-compose up -d &&

curl --request PUT --data 'http://application_api_0:5000,http://application_api_1:5000,http://application_api_2:5000,http://application_api_3:5000' http://localhost:8500/v1/kv/app_instances


