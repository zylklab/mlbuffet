model_list = ["iris.onnx", "diabetes.onnx"]
MODEL_FOLDER = "POTATOE"
session_list = []


def list_of_models(model_list, MODEL_FOLDER, session_list):
    for i in model_list:
        append_model(i, session_list, MODEL_FOLDER)


def append_model(model, session_list, MODEL_FOLDER):
    sess = MODEL_FOLDER
    cosa = [model, sess]
    session_list.append(cosa)


list_of_models(model_list, MODEL_FOLDER, session_list)
print(session_list)
