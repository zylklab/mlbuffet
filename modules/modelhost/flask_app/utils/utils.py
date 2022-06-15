from zipfile import ZipFile


def unzip_models(file_name):
    zip_ = ZipFile(file_name)
    zip_.extractall()
    return zip_.namelist()
