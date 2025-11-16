from flask import Flask, request, jsonify
app = Flask(__name__)



@app.route('/', methods=['GET'])
def hello_world():
    return 'User V2 Service is running!'

if __name__ == '__main__':
    print("Microservices user V2 !!!!")
    app.run(host='0.0.0.0', port=5001, debug=True)