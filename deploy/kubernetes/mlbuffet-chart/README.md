# MLBUFFET

Chart to deploy MLBuffet as Helm Chart. More info at https://github.com/zylklab/mlbuffet

### INSTALL MLBUFFET

To use MLBuffet chart:

1. Create MLBuffet namespace:
```bash
kubectl create ns mlbuffet
```
Or set the value `namespace.createNamespace` as `true`

2. Install MLBuffet chart:
```bash
helm install mlbuffet mlbuffet/ -n mlbuffet
```

### UNINSTALL MLBUFFET

Remove MLBuffet chart as usual:

```bash
helm uninstall mlbuffet -n mlbuffet
```
