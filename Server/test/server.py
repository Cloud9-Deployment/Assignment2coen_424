from flask import Flask, request, jsonify
app = Flask(__name__)



@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    print("Server running at http://localhost:5000 !!!!")
    app.run(host='0.0.0.0', port=5000, debug=True)