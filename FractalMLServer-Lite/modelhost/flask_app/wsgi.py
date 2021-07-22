import ssl
from app import server
from utils.constants import FLASK_PORT

if __name__ == "__main__":
    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.load_cert_chain(CERTFILE, KEYFILE)
    #HTTP
    server.run(debug=True, host='0.0.0.0', port=FLASK_PORT)

