import sqlalchemy
import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)


# Transaction Class/Model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    amount = db.Column(db.Integer)
    description = db.Column(db.String(200))
    is_incoming = db.Column(db.Boolean)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    def __init__(self, amount, description, is_incoming):
        self.amount = amount
        self.description = description
        self.is_incoming = is_incoming


# Transaction Schema
class TransactionSchema(ma.Schema):
    class Meta:
        fields = ('id', 'amount', 'description', 'is_incoming', 'created_date')


# Init schema
transaction_schema = TransactionSchema()
transactions_schema = TransactionSchema(many=True)


# Create a Transaction
@app.route('/transactions', methods=['POST'])
def add_transaction():
    amount = request.json['amount']
    description = request.json['description']
    is_incoming = request.json['is_incoming']

    new_transaction = Transaction(amount, description, is_incoming)
    db.session.add(new_transaction)
    db.session.commit()

    return transaction_schema.jsonify(new_transaction)


# Get all transactions
@app.route('/transactions', methods=['GET'])
def get_transactions():
    all_transactions = Transaction.query.all()
    result = transactions_schema.dump(all_transactions)
    return jsonify(result)


# Run server
if __name__ == '__main__':
    app.run(debug=True)
