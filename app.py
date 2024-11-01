from flask import Flask, render_template
from bot import testfun

app = Flask(__name__)

@app.route('/')
def home():
    return testfun()

@app.route('/about')
def about():
    return "<h1>About This App</h1><p>This is a simple Flask application to demonstrate basic routing.</p>"

if __name__ == '__main__':
    app.run(debug=True)
