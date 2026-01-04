# import scripts.movement
# import scripts.camera
from flask import Flask, make_response, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()