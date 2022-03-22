from flask import Flask, request, Response
import utils.buffetvc as bvc

server = Flask(__name__)


@server.route('/save/<tag>', methods=['PUT'])
def save(tag):
    file = request.files['path']
    filename = file.filename
    bvc.save_file(file=file, tag=tag, file_name=filename)
    return Response(f'File {filename} saved with the tag {tag}\n')


@server.route('/remove/<tag>', methods=['DELETE'])
def remove(tag):
    separator = tag.find(':')
    if separator < 0:
        version = 'default'
    else:
        name_splitted = tag.split(':')
        tag = name_splitted[0]
        version = name_splitted[1]

    bvc.remove_file(name=tag, version=version)
    return Response(f'{tag} removed\n')


@server.route('/download/<tag>', methods=['GET'])
def download(tag):
    separator = tag.find(':')
    if separator < 0:
        version = 'default'
    else:
        name_splitted = tag.split(':')
        tag = name_splitted[0]
        version = name_splitted[1]
    return bvc.download_file(name=tag, version=version)


@server.route('/default/<tag>/<new_default>', methods = ['POST'])
def update_default(tag, new_default):
    return bvc.update_default(name=tag, version=new_default)


if __name__ == '__main__':
    pass
