from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():  # put application's code here
    return render_template('home.html')

if __name__ == '__main__':
    app.run()