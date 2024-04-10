
import threading
from flask_restful import Api, Resource
from flask import Flask, jsonify

app = Flask(__name__)
api = Api(app)
transaction_lock = threading.Lock()


class Home(Resource):
    def get(self):
        return str("Task Manager")


api.add_resource(Home, "/")


@app.route('/acquire_lock', methods=['GET'])
def acquire_lock():
    if transaction_lock.acquire(blocking=False):  # Non-blocking acquire
        return jsonify({'message': 'Lock acquired successfully'}), 200
    else:
        return jsonify({'message': 'Lock is already held by another node'}), 409


@app.route('/release_lock', methods=['POST'])
def release_lock():
    transaction_lock.release()
    return jsonify({'message': 'Lock released successfully'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009)
