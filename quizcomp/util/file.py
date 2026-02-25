import quizcomp.util.encoding

def to_base64(path):
    with open(path, 'rb') as file:
        data = file.read()

    return quizcomp.util.encoding.to_base64(data)

def from_base64(data, path):
    data = quizcomp.util.encoding.from_base64(data)
    with open(path, 'wb') as file:
        file.write(data)

