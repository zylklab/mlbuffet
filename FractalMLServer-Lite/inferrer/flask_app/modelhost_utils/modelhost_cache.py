import hashlib
import json

# TODO: This can be REDIS or SQLite

default_cache_filename = '/.cache/inferrer-cache.json'


def get_hash(model_name, inputs):
    input_string = ' '.join(str(e) for e in inputs)
    hash_func_input = (model_name + input_string).encode('utf-8')
    return hashlib.blake2b(hash_func_input).hexdigest()


# Read prediction from json
def get_prediction(hash_code, filename=default_cache_filename):
    with open(filename, 'r') as file:
        cache_dict = json.load(file)
        return cache_dict.get(hash_code)  # return None if not present


# Write prediction as json format
def put_prediction_in_cache(hash_code=None, model=None, inputs=None, prediction=None, filename=default_cache_filename):
    with open(filename, 'r+') as file:
        # Load existing data
        cache_dict = json.load(file)

        # Add new cache entry
        new_data = {
            hash_code:
                {'model': model,
                 'inputs': inputs,
                 'prediction': prediction
                 }
        }
        cache_dict.update(new_data)

        # Save back to json
        file.seek(0)
        json.dump(cache_dict, file, indent=2)
