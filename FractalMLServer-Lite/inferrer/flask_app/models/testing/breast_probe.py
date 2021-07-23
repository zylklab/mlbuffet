from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
diabetes = load_diabetes()
X_train, X_test, y_train, y_test = train_test_split(diabetes.data, diabetes.target)

log_reg = RandomForestClassifier()
log_reg.fit(X_train, y_train)

print(X_test[0])
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
initial_type = [('float_input', FloatTensorType([None, 10]))]
onx = convert_sklearn(log_reg, initial_types=initial_type)
with open("diabetes.onnx", "wb") as f:
    f.write(onx.SerializeToString())


