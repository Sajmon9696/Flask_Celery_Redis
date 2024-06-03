from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from celery import Celery

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)


@app.route('/')
def home():
    return "Hello, World!"


@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/submit', methods=['POST'])
def submit_form():
    name = request.form['name']
    email = request.form['email']
    new_data = UserData(name=name, email=email)
    db.session.add(new_data)
    db.session.commit()
    return redirect(url_for('form'))



# Celery configuration
app.config['broker_url'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['broker_url'])
celery.conf.update(app.config)


@celery.task
def process_form_data(name, email):
    with app.app_context():
        new_data = UserData(name=name, email=email)
        db.session.expunge(new_data)
        db.session.add(new_data)
        db.session.commit()


@app.route('/async_form')
def async_form():
    return render_template('async_form.html')


@app.route('/submit_async', methods=['POST'])
def submit_async_form():
    name = request.form['name']
    email = request.form['email']
    process_form_data.delay(name, email)
    return redirect(url_for('form'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
