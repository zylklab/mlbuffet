import os
import time
import json
import shutil
import werkzeug.datastructures as ds

archivos_folder = "files"
extern_folder = 'modelhostfiles'


def save_file(file, tag, file_name):
    model_folder = os.path.join(archivos_folder, tag)
    # Creation of the name folder to the model and the history file
    if not os.path.exists(model_folder):
        os.makedirs(model_folder)
        history_file = os.path.join(model_folder, '.history')
        latest_file = os.path.join(model_folder, '.latest')
        open(history_file, 'x')
        open(latest_file, 'x')
        with open(history_file, "w") as hf:
            hf.write('{}')
        with open(latest_file, "w") as hf:
            hf.write('0')
    ts = time.time()
    time_string = time.strftime('%H:%M:%S %d/%m/%Y', time.localtime(ts))
    with open(os.path.join(model_folder, '.latest'), 'r') as fl:
        last_folder = int(fl.read())
        new_folder = str(last_folder + 1)
        folder_dir = os.path.join(model_folder, new_folder)

    if not os.path.exists(folder_dir):
        os.makedirs(folder_dir)
    file.save(os.path.join(folder_dir, file_name))

    with open(os.path.join(model_folder, '.history'), 'r+') as fh:
        data = json.load(fh)
        data[new_folder] = {"folder": folder_dir, "file": file_name, "time": time_string, "timestamp": ts}
        fh.seek(0)
        fh.write(json.dumps(data, sort_keys=True))
        fh.close()

    with open(os.path.join(model_folder, '.latest'), 'w') as fl:
        fl.write(new_folder)


def remove_file(name, version):
    latest_file = os.path.join(archivos_folder, name, '.latest')
    history_file = os.path.join(archivos_folder, name, '.history')

    folders = []

    with open(history_file, 'r') as fh:
        data_json = json.load(fh)
        for i in data_json:
            i = int(i)
            folders.append(i)
        if version == 'latest':
            version = folders[-1]
        del data_json[str(version)]

    with open(latest_file, 'r') as fl:
        data = fl.read()
        if data == version or version == 'latest':
            version = data
        fl.close()
    with open(latest_file, 'w') as fl:
        if int(data) == int(version):
            fl.write(str(folders[-1]-1))
        else:
            fl.write(data)
        fl.close()

    with open(history_file, 'w') as fh:
        fh.write(json.dumps(data_json, sort_keys=True))
        fh.close()
    folder_file = os.path.join(archivos_folder, name, str(version))
    shutil.rmtree(folder_file)
