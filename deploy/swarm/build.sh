docker build -t mlbuffet_inferrer  ../../inferrer/flask_app/
docker build -t mlbuffet_modelhost ../../modelhost/flask_app/
docker build -t mlbuffet_metrics ../../metrics/prometheus/
docker build -t mlbuffet_cache ../../cache/
