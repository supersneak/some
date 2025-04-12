from second import app, db
from flask import Flask, render_template, request , redirect, url_for, jsonify 

#ここはテーブルの設計図を作った状態（まだテーブルは作成されていない）
class List(db.Model): #db.Modelをつかうことでこのクラスが、データベースのテーブルとして機能する（クラスの継承）
    id = db.Column(db.Integer, primary_key=True) #primary_keyは主キーという意味（識別用）
    name = db.Column(db.String(100), nullable=False) #nullableは空を許すか
    items = db.relationship('DO', backref='list', lazy=True) #relationshipでデータベース間の親子関係を作っており、backref='list' は、DO クラスに list という属性を追加している。この属性によって、子→親にアクセスできる 
    #↑が外部キーになっている
    
class DO(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    order = db.Column(db.Integer) #Integer=整数という意味　ここでは並び替えを保存するための新しいカラムを作成している(順番を識別するため)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=True)
    completed = db.Column(db.Boolean, default=False)
    
#ここでテーブルの作成が行われている
#list.id のlistは上のクラスのListを表している。読み込むときに小文字に変換されている。
#with app.app_context():→flaskのアプリケーションコンテキストを作っている
with app.app_context():
    db.create_all()  

#index.htmlが読み込まれるとき、必ず読み込まれる
@app.route('/', methods=['GET', 'POST'])
def index():
    lists = List.query.all()  # すべてのリストを取得
    selected_list = None  # 初期状態ではリストは選ばれていない
    dos = []  # アイテムは初期状態では空
    
    #リストが選択されたときの処理
    if request.method == 'POST':
        list_id = request.form.get('list_id')  # 選択されたリストのIDを取得
        selected_list = List.query.get(list_id) #list_idを使いデータベースからリストを取得
        if selected_list:  # selected_list が None でないことを確認
            dos = DO.query.filter_by(list_id=selected_list.id).order_by(DO.order).all()# list_idに紐づくアイテムをすべて取得する
        else:
            dos = []  # エラー回避のため空リスト
        
    elif request.args.get('list_id'):  # リストが選択されていた場合
        selected_list = List.query.get(request.args.get('list_id'))  # クエリパラメータからリストIDを取得
        dos = DO.query.filter_by(list_id=selected_list.id).order_by(DO.order).all()
        
    return render_template('index.html', lists=lists, dos=dos, selected_list=selected_list) #Flaskが index.html をレンダリング（再読み込み）するときに、引数として lists, dos, selected_list のデータを渡す という意味

#新規リストの作成
@app.route('/create-list', methods=['POST'])
def create_list():
    list_name = request.form.get("list_name")
    
    if list_name:
        new_list = List(name=list_name)  # リスト名を使って新しいリストを作成
        db.session.add(new_list)  # リストをデータベースに保存
        db.session.commit()  # 
    return redirect(url_for('index'))  # 作成後にリダイレクト

#リスト内の要素の作成
@app.route('/create', methods=['POST'])
def add():
    title = request.form.get("title")
    list_id = request.form.get("list_id")
        
    if title and list_id:
        # ここで現在のデータベース並び替え時の数を取得
        max_order = db.session.query(db.func.max(DO.order)).scalar() or 0
        new_do = DO(title=title, order=max_order + 1, list_id=list_id)
        db.session.add(new_do)
        db.session.commit()  

    return redirect(url_for('index', list_id=list_id))  # アイテム追加後、リストIDを保持したままリダイレクト

#リスト内の要素の削除
@app.route('/del', methods=['POST'])
def delete():
    id = request.form.get("id")  # フォームから ID を取得
    if id:
        delete = DO.query.get(id)  # ID に一致するデータを取得
        if delete:
            list_id = delete.list_id
            db.session.delete(delete)  # データを削除
            db.session.commit()  # 変更を保存
    return redirect(url_for('index', list_id=list_id))  # 削除後にリロード


@app.route('/reorder', methods=['POST'])
def reorder():
    data = request.get_json()  # クライアントから送られてきた並び順データを取得（辞書の形で）
    order = data['order']  # 並び順のデータ（リスト）（'order'は辞書のキーの名前になる）送られてきてるの→「body: JSON.stringify({ order: order }) 」

    # 並び順に従ってデータベースの順番を更新
    for index, item_id in enumerate(order):# enumerateは配列の位置も返すから、indexには0から番号が入っていく
        item = DO.query.get(item_id)
        if item:
            item.order = index  # 新しい順番を設定　データベースのorderの値が変わる
            db.session.commit()  # データベースに保存

    return jsonify({'status': 'success', 'order': order})

#リストの削除
@app.route('/deletelist', methods=['POST'])
def deletelist():
    list_id = request.form.get("deletelist")
    if list_id:
        list_to_delete = List.query.get(list_id)
        if list_to_delete:
            DO.query.filter_by(list_id=list_to_delete.id).delete()
            db.session.delete(list_to_delete)
            db.session.commit()
    return redirect(url_for('index'))


@app.route('/update', methods=['POST'])
def update():
    todo_id = request.form.get('id')      #要素のIDの取得
    list_id = request.form.get('list_id')  #リストIDを取得
    todo = DO.query.get(todo_id)

    if todo:
        # チェックボックスがオンの場合、completedをTrueに
        if request.form.get('completed') == 'on':
            todo.completed = True
        else:
            # チェックボックスがオフの場合、completedをFalseに
            todo.completed = False
        
        db.session.commit()
    
    return redirect(url_for('index', list_id=list_id))  # 選択中のリストを維持したままリロード
       
