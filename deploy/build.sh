docker build -t localhost:5000/mlbuffet_inferrer  ../modules/inferrer/flask_app/
docker build -t localhost:5000/mlbuffet_modelhost ../modules/modelhost/flask_app/
docker build -t localhost:5000/mlbuffet_metrics ../modules/metrics/prometheus/
docker build -t localhost:5000/mlbuffet_cache ../modules/cache/
docker build -t localhost:5000/mlbuffet_storage ../modules/storage/flask_app/
docker build -t localhost:5000/mlbuffet_trainer ../modules/trainer/
