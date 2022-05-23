kubectl apply -f ./autodeploy/mlbuffet_namespace.yaml
kubectl apply -f ./autodeploy/volume.yaml
kubectl apply -f ./autodeploy/rbac.yaml
kubectl apply -f ./autodeploy/modelhost.yaml
kubectl apply -f ./autodeploy/metrics.yaml
kubectl apply -f ./autodeploy/inferrer.yaml
kubectl apply -f ./autodeploy/storage.yaml
kubectl apply -f ./autodeploy/cache.yaml
