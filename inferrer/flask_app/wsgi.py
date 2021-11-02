from app import server
from utils.constants import FLASK_PORT

if __name__ == "__main__":
    server.run(debug=True, host='0.0.0.0', port=FLASK_PORT)  # HTTP
