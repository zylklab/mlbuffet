import tensorflow

# List with preloaded models to do the inference
model_sessions = {}


def load_new_model(tag, filename):
    return 'To be done!'


def check_model_exists(tag):
    # Check that the model exists
    if tag not in model_sessions.keys():
        return False
    else:
        return True


def perform_inference(tag, model_input):
    return 'To be done!'
