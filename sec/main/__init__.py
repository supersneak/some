from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object('second.config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

import second.main

#マイグレーション=データベースに新しい情報を追加するときに使うもの
#つまり、後からデータベースの構造を変更するときに使う