import sklearn_conversor

model = "model-knn.pkl"
model_out = "probe.onnx"
feat = 4

sklearn_conversor.sk_conversor(model, model_out, 4)