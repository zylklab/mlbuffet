docker build -t mlbuffet_inferrer  ../../modules/inferrer/flask_app/
docker build -t mlbuffet_modelhost ../../modules/modelhost/flask_app/
docker build -t mlbuffet_prometheus ../../modules/metrics/prometheus/
docker build -t mlbuffet_cache ../../modules/cache/
docker build -t mlbuffet_storage ../../modules/storage/flask_app/
docker build -t mlbuffet_trainer ../../modules/trainer/flask_app/
