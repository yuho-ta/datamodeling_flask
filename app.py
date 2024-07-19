
import sqlite3
from typing import Final, Optional, Union
import unicodedata
from datetime import datetime, timedelta 
from flask import Flask, g, redirect, render_template, request, url_for, flash
from werkzeug import Response

# データベースのファイル名
DATABASE: Final[str] = 'fun.db'

# Flask クラスのインスタンス
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def get_db() -> sqlite3.Connection:
    """
    データベース接続を得る.

    リクエスト処理中にデータベース接続が必要になったら呼ぶ関数。

    Flask の g にデータベース接続が保存されていたらその接続を返す。
    そうでなければデータベース接続して g に保存しつつ接続を返す。
    その際に、カラム名でフィールドにアクセスできるように設定変更する。

    https://flask.palletsprojects.com/en/3.0.x/patterns/sqlite3/
    のサンプルにある関数を流用し設定変更を追加。

    Returns:
      sqlite3.connect: データベース接続
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # カラム名でアクセスできるよう設定変更
    return db


@app.teardown_appcontext
def close_connection(exception: Optional[BaseException]) -> None:
    """
    データベース接続を閉じる.

    リクエスト処理の終了時に Flask が自動的に呼ぶ関数。

    Flask の g にデータベース接続が保存されていたら閉じる。

    https://flask.palletsprojects.com/en/3.0.x/patterns/sqlite3/
    のサンプルにある関数をそのまま流用。

    Args:
      exception (Optional[BaseException]): 未処理の例外
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
        

        


def has_control_character(s: str) -> bool:
    """
    文字列に制御文字が含まれているか否か判定する.

    Args:
      s (str): 判定対象文字列
    Returns:
      bool: 含まれていれば True 含まれていなければ False
    """
    return any(map(lambda c: unicodedata.category(c) == 'Cc', s))


@app.route('/')
def index() -> str:
    """
    入口のページ.

    `http://localhost:5000/` へのリクエストがあった時に Flask が呼ぶ関数。

    テンプレート index.html
    （本アプリケーションの説明や他ページへのリンクがある）
    をレンダリングして返す。

    Returns:
      str: ページのコンテンツ
    """
    # テンプレートへ何も渡さずにレンダリングしたものを返す
    return render_template('index.html')


@app.route('/artists')
def artists() -> str:
    """
    artist一覧のページ（全員）.

    Returns:
      str: ページのコンテンツ
    """
    # データベース接続してカーソルを得る
    cur = get_db().cursor()

    
    a_list = cur.execute('SELECT id,name,debut_year FROM Artist').fetchall()

    # 一覧をテンプレートへ渡してレンダリングしたものを返す
    return render_template('artists.html', a_list=a_list)

@app.route('/artists/<id>')
def artist(id: str) -> str:
    """
    artist詳細ページ.
    Returns:
      str: ページのコンテンツ
    """
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    try:
        # 文字列型で渡された社員番号を整数型へ変換する
        id_num = int(id)
    except ValueError:
       
        return render_template('artist-not-found.html')

    
    artist = cur.execute('SELECT * FROM Artist WHERE id = ?',
                           (id_num,)).fetchone()

   
    return render_template('artist.html', artist = artist)

@app.route('/events/<id>')
def events(id: str) -> str:
    """
    Show events for a specific artist.
    """
    con = get_db()
    cur = con.cursor()

    try:
        id_num = int(id)
    except ValueError:
        return render_template('artist-not-found.html')

    # Fetch artist details
    artist = cur.execute('SELECT * FROM Artist WHERE id = ?', (id_num,)).fetchone()
    if artist is None:
        return render_template('artist-not-found.html')

    # Fetch all event types for dropdown
    event_list = cur.execute('SELECT type_name FROM EventType').fetchall()

    # Fetch all events associated with the artist
    e_list = cur.execute('SELECT e.name AS event_name FROM Event e WHERE e.group_id = ?', (id_num,)).fetchall()

    return render_template('events.html', id=id_num, event_list=event_list, e_list=e_list)

@app.route('/events/<id>', methods=['POST'])
def events_filtered(id: str) -> str:
    """
    Show events filtered by event type for a specific artist.
    """
    con = get_db()
    cur = con.cursor()

    try:
        id_num = int(id)
    except ValueError:
        return render_template('artist-not-found.html')

    artist = cur.execute('SELECT * FROM Artist WHERE id = ?', (id_num,)).fetchone()
    if artist is None:
        return render_template('artist-not-found.html')

    # Fetch all event types for dropdown
    event_list = cur.execute('SELECT type_name FROM EventType').fetchall()

    # Get selected event type from form
    event_type = request.form.get('event_type', '')

    if event_type:
        # Fetch events filtered by event type
        e_list = cur.execute('''
            SELECT e.name AS event_name
            FROM Event e
            JOIN EventType et ON e.type_id = et.id
            WHERE e.group_id = ? AND et.type_name = ?
        ''', (id_num, event_type)).fetchall()
    else:
        # If no event type is selected, show all events
        e_list = cur.execute('SELECT e.name AS event_name FROM Event e WHERE e.group_id = ?', (id_num,)).fetchall()

    return render_template('events.html', id=id_num, event_list=event_list, e_list=e_list)



@app.route('/login', methods=['GET','POST'])
def login() -> str:
    """
    Process login form submission.

    Returns:
      str: Redirect or error message
    """
    # Database connection and cursor retrieval
    con = get_db()
    cur = con.cursor()
    if request.method == 'POST':
       member_id = request.form['id_filter']
       phone_number = request.form['phone_filter']

       customer = cur.execute('SELECT * FROM Customer WHERE id = ?',
                              (member_id,)).fetchone()

       if customer and customer['phone'] == phone_number:
        
           return redirect(url_for('customer', id=member_id))
       else:
            flash('ユーザーIDまたは電話番号が間違っています。')
            return redirect(url_for('login'))
          
    return render_template('login.html')




@app.route('/logout')
def logout():

    return redirect(url_for('index'))

@app.route('/customer/<id>')
def customer(id: str) -> str:
    
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()
    id_num = int(id)
    
    # Fetch customer details
    customer = cur.execute('SELECT * FROM Customer WHERE id = ?', (id_num,)).fetchone()
    cnt = cur.execute('''
        SELECT COUNT(s.id) AS subscription_count
        FROM
            Subscription s
        WHERE
            s.customer_id = ?
    ''', (id_num,)).fetchone()[0]
    # Fetch subscriptions of the customer
    s_list = cur.execute('''
        SELECT
            s.id AS subscription_id,
            a.name AS artist_name,
            sc.course_name,
            s.start_date,
            s.end_date
        FROM
            Subscription s
            JOIN Artist a ON s.group_id = a.id
            JOIN SubscriptionCourse sc ON s.course_id = sc.id
        WHERE
            s.customer_id = ?
    ''', (id_num,)).fetchall()

    # Dictionary to store events for each subscription
    e_dict = {}
    
    # Fetch events for each subscription
    for subscription in s_list:
        subscription_id = subscription['subscription_id']
        events = cur.execute('''
            SELECT
                e.name AS event_name,
                et.type_name AS type_name,
                ep.participation_date AS participation_date
            FROM
                EventParticipation ep
                JOIN Event e ON ep.event_id = e.id
                JOIN EventType et ON e.type_id = et.id
            WHERE
                ep.subscription_id = ?
        ''', (subscription_id,)).fetchall()
        e_dict[subscription_id] = events

    return render_template('customer.html', customer=customer, s_list=s_list, e_dict=e_dict, cnt = cnt)
   



@app.route('/customer_add')
def customer_add() -> str:
   
    """
    入会ページ

    Returns:
      str: ページのコンテンツ
    """
    # テンプレートへ何も渡さずにレンダリングしたものを返す
    return render_template('customer-add.html')


@app.route('/customer-add', methods=['POST'])
def customer_add_execute() -> Response:
    """
    入会実行.

    `http://localhost:5000/employee-add` への POST メソッドによる
    リクエストがあった時に Flask が呼ぶ関数。
    追加する社員の情報が POST パラメータの
    `id`, `name`, `salary`, `manager_id`, `birth_year`, `start_year`
    に入っている。

    データベース接続を得て、POST パラメータの各内容をチェック、
    問題なければ新しい社員として追加し、
    employee_add_results へ処理結果コードを入れてリダイレクトする。
    （PRG パターンの P を受けて R を返す）

    Returns:
      Response: リダイレクト情報
    """
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    # リクエストされた POST パラメータの内容を取り出す
    id_str = request.form['id']
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    
    try:
        id = int(id_str)
    except ValueError:
        flash('実行に失敗しました。無効なIDが指定されました。')
        return redirect(url_for('customer_add'))
    if id <= 0:
        flash('実行に失敗しました。無効なIDが指定されました。')
        return redirect(url_for('customer_add'))
    customer = cur.execute('SELECT id FROM Customer WHERE id = ?',
                           (id,)).fetchone()
    if customer is not None:
        flash('実行に失敗しました。すでに既存のIDが指定されました。')
        return redirect(url_for('customer_add'))
    
    if has_control_character(name):
        flash('実行に失敗しました。名前に使えない文字があります。')
        return redirect(url_for('customer_add'))
    
    if has_control_character(email):
        flash('実行に失敗しました。メールアドレスに使えない文字があります。')
        return redirect(url_for('customer_add'))
    
    
    if has_control_character(address):
        flash('実行に失敗しました。住所に使えない文字があります。')
        return redirect(url_for('customer_add'))
    
    
    
   
    try:
        cur.execute('INSERT INTO Customer '
                    '(id, name, email, phone, address) '
                    'VALUES (?, ?, ?, ?, ?)',
                    (id, name, email, phone, address))
    except sqlite3.Error:
        flash('データベースエラー')
        return redirect(url_for('customer_add'))
    
   
    con.commit()
    
    # 社員追加完了
    return redirect(url_for('customer', id=id))





@app.route('/customer-edit/<id>')
def customer_edit(id: str) -> str:
    """
    会員情報編集ページ.
    Returns:
      str: ページのコンテンツ
    """
    
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()
   
    try:
        id_num = int(id)
    except ValueError:
        flash('実行に失敗しました。無効なIDが指定されました。')
        return redirect(url_for('customer_edit', id = id))
    
    customer = cur.execute('SELECT * FROM Customer WHERE id = ?',
                           (id_num,)).fetchone()
    if customer is None:
        flash('実行に失敗しました。会員情報が見つかりません。')
        return redirect(url_for('customer_edit', id = id_num))

   
    return render_template('customer-edit.html', id = id, customer = customer)


@app.route('/customer-edit/<id>', methods=['POST'])
def customer_edit_update(id: str) -> Response:
    """
    会員編集更新.

    Returns:
      Response: リダイレクト情報
    """
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    try:
        id_num = int(id)
    except ValueError:
        flash('実行に失敗しました。無効なIDが指定されました。')
        return redirect(url_for('customer-edit', id = id_num))
    
    customer = cur.execute('SELECT * FROM Customer WHERE id = ?',
                           (id_num,)).fetchone()
    if customer is None:
        flash('実行に失敗しました。会員情報が見つかりません。')
        return redirect(url_for('customer_edit', id = id_num))
    
    name = request.form['name']
    address = request.form['address']
    phone = request.form['phone']
    email = request.form['email']
   
    if has_control_character(name):
        flash('実行に失敗しました。名前に使えない文字があります。')
        return redirect(url_for('customer_edit', id = id_num))
    
    if has_control_character(email):
        flash('実行に失敗しました。メールアドレスに使えない文字があります。')
        return redirect(url_for('customer_edit', id = id_num))
    
    
    if has_control_character(address):
        flash('実行に失敗しました。住所に使えない文字があります。')
        return redirect(url_for('customer_edit', id = id_num))
    
        
    try:

        cur.execute('UPDATE Customer '
                    'SET name = ?, email = ?, '
                    'phone = ?, address = ? '
                    'WHERE id = ?',
                    (name, email, phone, address, id_num))
        con.commit()
    except sqlite3.Error:
        flash('実行に失敗しました。')
        return redirect(url_for('customer_edit', id = id_num))


    flash('会員情報が編集されました！')
    return redirect(url_for('customer',id = id_num))

@app.route('/join-funclub/<id>')
def join_funclub(id: str) -> str:
    """
    Show events for a specific artist.
    """
    
    con = get_db()
    cur = con.cursor()
  
    
    id_num = int(id)
  
    artist_list = cur.execute('SELECT name FROM Artist').fetchall()
    course_list = cur.execute('SELECT *  FROM SubscriptionCourse').fetchall()
   
    return render_template('join-funclub.html', id=id_num, artist_list = artist_list, course_list = course_list)

@app.route('/join-funclub/<id>', methods=['POST'])
def join_funclub_execute(id: str) -> str:
    """
    Show events filtered by event type for a specific artist.
    """
    con = get_db()
    cur = con.cursor()
    
    id_num = int(id)
  
    artist_list = cur.execute('SELECT name FROM Artist').fetchall()
    course_list = cur.execute('SELECT *  FROM SubscriptionCourse').fetchall()
    try:
        subscription_id = int(request.form.get('id',''))
    except ValueError:
        flash('実行に失敗しました。無効なIDが指定されました。')
        return redirect(url_for('join_funclub',id = id_num))
    if subscription_id <= 0:
        flash('実行に失敗しました。無効なIDが指定されました。')
        return redirect(url_for('join_funclub',id = id_num))
    subscriber = cur.execute('SELECT id  FROM Subscription WHERE id = ?', (subscription_id,)).fetchone()
    if subscriber is not None:
        flash('実行に失敗しました。すでに既存のIDが指定されました。')
        return redirect(url_for('join_funclub',id = id_num))
    
    artist_name = request.form.get('artist', '')
    course_name = request.form.get('course', '')
    start_date_str = request.form.get('start_date', '')
    
   
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('日付の形式が正しくありません。YYYY-MM-DDの形式で入力してください。')
        return redirect(url_for('join_funclub', id=id_num))
    
    
    duration_month = int(cur.execute('SELECT duration_months FROM SubscriptionCourse WHERE course_name = ?', (course_name,)).fetchone()['duration_months'])
    end_date = start_date + timedelta(days=duration_month * 30)
    
      
    artist_id = cur.execute('SELECT id FROM Artist WHERE name = ?', (artist_name,)).fetchone()['id']
    
    course_id = cur.execute('SELECT id FROM SubscriptionCourse WHERE course_name = ?', (course_name,)).fetchone()['id']
    
    is_double = cur.execute('SELECT id  FROM Subscription WHERE customer_id = ? and group_id = ? and start_date < ? and end_date > ? ', (id_num,artist_id,end_date,start_date)).fetchone()
    if is_double:
       flash('実行に失敗しました。すでに同じ期間中に会員資格が存在します。')
       return redirect(url_for('join_funclub', id=id_num))
   
    try:
        cur.execute('INSERT INTO Subscription '
                    '(id,customer_id, group_id, course_id, start_date, end_date) '
                    'VALUES (?,?, ?, ?, ?, ?)',
                    (subscription_id,id_num, artist_id, course_id, start_date, end_date))
        con.commit()
    except sqlite3.Error:
        flash('データベースエラー')
        return redirect(url_for('join_funclub', id=id_num))
    
    flash('Fun Clubに参加しました！')
    return redirect(url_for('customer', id=id_num))

@app.route('/customer-del/<id>')
def customer_del(id: str) -> str:
    """
    退会確認ページ.

    Returns:
      str: ページのコンテンツ
    """
    con = get_db()
    cur = con.cursor()
    id_num = int(id)
    
    subscribers = cur.execute('SELECT id AS subscription_id ,customer_id AS customer_id FROM Subscription WHERE id = ?', (id_num,)).fetchall()
    return render_template('customer-del.html', id=id_num, customer_id = subscribers[0]['customer_id'])


@app.route('/customer-del/<id>', methods=['POST'])
def customer_del_execute(id: str) -> Response:
    """
    退会実行.

    Returns:
      Response: リダイレクト情報
    """
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    try:
        id_num = int(id)
    except ValueError:
        flash('実行に失敗しました。無効なIDが指定されました。')
        return redirect(url_for('customer_del', id = id))
   
    customer = cur.execute('SELECT *  FROM Subscription WHERE id = ?',
                           (id_num,)).fetchone()
    if customer is None:
        flash('実行に失敗しました。会員情報が見つかりません。')
        return redirect(url_for('customer_del', id = id_num))

    try:
        cur.execute('DELETE FROM Subscription WHERE id = ?', (id_num,))
    except sqlite3.Error:
        flash('退会に失敗しました。')
        return redirect(url_for('customer_del', id = id_num))
    
    con.commit()
    flash('退会が完了しました')
    return redirect(url_for('customer',id = customer['customer_id']))

if __name__ == '__main__':
    # このスクリプトを直接実行したらデバッグ用 Web サーバで起動する
    app.run()

