docker build -t mlbuffet_inferrer:arm64  ../../inferrer/flask_app/
docker build -t mlbuffet_modelhost:arm64 ../../modelhost/flask_app/
docker build -t mlbuffet_prometheus:arm64 ../../metrics/prometheus/
docker build -t mlbuffet_cache:arm64 ../../cache/
docker build -t mlbuffet_storage:arm64 ../../storage/
