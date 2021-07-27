import json

import hashlib


class modelhost_cache:

    def __init__(self):
        pass

    def get_hash(self=None, model=None, input=None):
        inputstr = " ".join(str(e) for e in input)
        prehash = model + inputstr
        prehashb = prehash.encode("utf-8")
        hash = hashlib.blake2b(prehashb).hexdigest()
        return hash

    def data_structure(self=None, hash=None, model=None, input=None, prediction=None):
        dict = {"hash": hash, "data": {"model": model, "input": input, "prediction": prediction}}
        return dict

    # Escribe la predicción en el json
    def put_prediction(self=None, new_data=None, filename='/.cache/inferrer-cache.json'):
        with open(filename, 'r+') as file:
            # First we load existing data into a dict.
            file_data = json.load(file)
            # Join new_data with file_data inside emp_details
            file_data.append(new_data)
            # Sets file's current position at offset.
            file.seek(0)
            # convert back to json.
            json.dump(file_data, file, indent=2)

    # Coge la predicción del json
    def get_prediction(self=None, hash=None, filename='/.cache/inferrer-cache.json'):
        with open(filename, "r") as f:
            file_data = json.load(f)
            for i in file_data:
                if i["hash"] == hash:
                    a = i["data"]["prediction"]
                    return a

    # Comprueba la existencia del hash en el json
    def check_hash(self=None, hash=None, filename="/.cache/inferrer-cache.json"):
        with open(filename, "r") as f:
            file_data = json.load(f)
            for i in file_data:
                if i["hash"] == hash:
                    return "Key exists"

