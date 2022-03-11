from flask import Flask, request, Response
import buffetvc

server = Flask(__name__)


@server.route('/save/<tag>', methods=['PUT'])
def save(tag):
    file = request.files['path']
    filename = file.filename
    buffetvc.save_file(file=file, tag=tag, file_name=filename)
    return Response(f'File {filename} saved with the tag {tag}\n')


@server.route('/remove/<tag>', methods=['DELETE'])
def remove(tag):
    separator = tag.find(':')
    if separator < 0:
        version = 'latest'
    else:
        name_splitted = tag.split(':')
        tag = name_splitted[0]
        version = name_splitted[1]

    buffetvc.remove_file(name=tag, version=version)
    return Response(f'{tag} removed\n')


if __name__ == '__main__':
    server.run()
