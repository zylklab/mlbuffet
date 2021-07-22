import joblib


class ModelManager:
    def __init__(self):
        self.MODEL_PATH = "./models/"
        self.classifer = None
        self.classifer_name = None

    def load_model(self, filename):
        if filename != self.classifer_name:  # si no está ya cargado
            self.classifer = joblib.load(self.MODEL_PATH + filename)
            self.classifer_name = filename

    def get_prediction(self, new_observations):
        if self.classifer is not None:
            result = self.classifer.predict(new_observations)
        else:
            result = "no model is loaded"
        return result

# EJEMPLOS
# [ 5.2,  3.2,  1.1,  0.1] #setosa
# [ 7.0, 3.2, 4.7, 1.4]    #versicolor
# [ 6.3, 3.3, 6.0, 2.5]    #virginica
