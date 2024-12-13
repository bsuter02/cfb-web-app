from flask import Flask, render_template
import get_rankings
app = Flask(__name__)

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():  # put application's code here
    return render_template('home.html')

@app.route('/ap', methods=['GET', 'POST'])
def ap():
    pic_links = get_rankings.get_ap_top_25()
    return render_template('AP.html', pic_links=pic_links)

if __name__ == '__main__':
    app.run()