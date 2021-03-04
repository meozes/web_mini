from flask import Flask, render_template, jsonify, request, session, redirect, url_for

import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient

# JWT 패키지를 사용합니다. (설치해야할 패키지 이름: PyJWT)
import jwt

# 토큰에 만료시간을 줘야하기 때문에, datetime 모듈도 사용합니다.
import datetime

# 회원가입 시엔, 비밀번호를 암호화하여 DB에 저장해두는 게 좋습니다.
# 그렇지 않으면, 개발자(=나)가 회원들의 비밀번호를 볼 수 있으니까요.^^;
import hashlib

from werkzeug.utils import secure_filename
#from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'SPARTA'

client = MongoClient('mongodb://54.180.160.114', 27017, username="test", password="test")
db = client.usersdata


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})

        comments = list(db.comment.find({}, {'_id': False}))
        comments.reverse()

        return render_template('index.html', user_info=user_info, comments=comments)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:


        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


## 로그인, 회원가입

@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/signup')
def signup():
    return render_template("signup.html")


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"id": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/sign_up/check_dup2', methods=['POST'])
def check_dup2():
    usernick_receive = request.form['usernick_give']
    exists = bool(db.users.find_one({"nick": usernick_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    db.users.insert_one({'id': username_receive, 'pw': pw_hash, 'nick': nickname_receive})

    return jsonify({'result': 'success'})


@app.route('/log_in', methods=['POST'])
def log_in():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.users.find_one({'id': id_receive, 'pw': pw_hash})

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        # token을 줍니다.
        return jsonify({'result': 'success', 'token': token, 'data': result['id']})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})



##음악

@app.route('/music/show1', methods=['GET'])
def show_list1():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # posts = list(db.sjlist.find({}).sort("date", -1).limit(20))  # 최신20개 가져온다
        # posts = list(db.sjlist.find({}).sort("date", -1))  # 최신20개 가져온다
        musics = list(db.mlist1.find({}, {'_id': False}))
        musics.reverse()
        # for post in posts:
        #     post["_id"] = str(post["_id"])  ##포스트구별 식별자인 _id, 각각의 id문자열로 바꾼다

        # return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts": posts})
        # return render_template('index.html', all_musics=musics)
        # return jsonify({"result": "success", 'all_musics': musics})

        return jsonify({"result": "success", 'all_musics': musics})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


    # # musics = list(db.sjlist.find({{'nick': }},{'_id':False}))
    # musics = list(db.sjlist.find({}, {'_id': False}))
    # return jsonify({'all_musics': musics})

@app.route('/music/show2', methods=['GET'])
def show_list2():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # posts = list(db.sjlist.find({}).sort("date", -1).limit(20))  # 최신20개 가져온다
        # posts = list(db.sjlist.find({}).sort("date", -1))  # 최신20개 가져온다
        musics = list(db.mlist2.find({}, {'_id': False}))
        musics.reverse()
        # for post in posts:
        #     post["_id"] = str(post["_id"])  ##포스트구별 식별자인 _id, 각각의 id문자열로 바꾼다

        # return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts": posts})
        # return render_template('index.html', all_musics=musics)
        # return jsonify({"result": "success", 'all_musics': musics})

        return jsonify({"result": "success", 'all_musics': musics})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


    # # musics = list(db.sjlist.find({{'nick': }},{'_id':False}))
    # musics = list(db.sjlist.find({}, {'_id': False}))
    # return jsonify({'all_musics': musics})

@app.route('/music/show3', methods=['GET'])
def show_list3():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # posts = list(db.sjlist.find({}).sort("date", -1).limit(20))  # 최신20개 가져온다
        # posts = list(db.sjlist.find({}).sort("date", -1))  # 최신20개 가져온다
        musics = list(db.mlist3.find({}, {'_id': False}))
        musics.reverse()

        # {"_id": -1}
        # for post in posts:
        #     post["_id"] = str(post["_id"])  ##포스트구별 식별자인 _id, 각각의 id문자열로 바꾼다

        # return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts": posts})
        # return render_template('index.html', all_musics=musics)
        # return jsonify({"result": "success", 'all_musics': musics})

        return jsonify({"result": "success", 'all_musics': musics})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


    # # musics = list(db.sjlist.find({{'nick': }},{'_id':False}))
    # musics = list(db.sjlist.find({}, {'_id': False}))
    # return jsonify({'all_musics': musics})

@app.route('/music/show4', methods=['GET'])
def show_list4():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # posts = list(db.sjlist.find({}).sort("date", -1).limit(20))  # 최신20개 가져온다

        musics = list(db.mlist4.find({}, {'_id': False}))
        musics.reverse()

        # for post in posts:
        #     post["_id"] = str(post["_id"])  ##포스트구별 식별자인 _id, 각각의 id문자열로 바꾼다

        # return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts": posts})
        # return render_template('index.html', all_musics=musics)
        # return jsonify({"result": "success", 'all_musics': musics})

        return jsonify({"result": "success", 'all_musics': musics})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


    # # musics = list(db.sjlist.find({{'nick': }},{'_id':False}))
    # musics = list(db.sjlist.find({}, {'_id': False}))
    # return jsonify({'all_musics': musics})


@app.route('/music', methods=['POST'])
def post_list():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})

        url_receive = request.form['url_give']
        db_receive = request.form['db_give']

        if db_receive =="#상쾌한":
            db_receive = "mlist1"
        elif db_receive == "#달달한":
            db_receive = "mlist2"
        elif db_receive == "#나른한":
            db_receive = "mlist3"
        elif db_receive == "#센치한":
            db_receive = "mlist4"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
        data = requests.get(url_receive, headers=headers)

        soup = BeautifulSoup(data.text, 'html.parser')

        img = soup.select_one('#body-content > div.song-main-infos > div.photo-zone > a')['href']
        # img = img[2:len(img)]
        title = soup.select_one('#body-content > div.song-main-infos > div.info-zone > h2').text.strip()
        artist = soup.select_one(
            '#body-content > div.song-main-infos > div.info-zone > ul > li:nth-child(1) > span.value').text.strip()

        doc = {
            'img': img,
            'title': title,
            'artist': artist,
            'nick': user_info['nick']
        }
        db[db_receive].insert_one(doc)
        return jsonify({'msg': '저장 완료!'})
            #return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))



##코멘트

@app.route('/comment', methods=['POST'])
def write_comment():
    token_receive =  request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info=db.users.find_one({"id":payload["id"]})

        user_nick = user_info["nick"]
        comment_receive =request.form['comment_give']

        doc={
            'comment':comment_receive,
            'user_nick':user_nick
        }
        db.comment.insert_one(doc)

        return jsonify({"result":"success", 'msg':'댓글이 등록되었습니다'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/comment/remove', methods=['POST'])
def delete_comment():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})
        # user_nick = user_info["nick"]

        del_receive = request.form['del_give']

        # db.users.delete_one({'name': 'bobby'})
        db.comment.remove({'_id': del_receive})
        return jsonify({"result": "success", 'msg': '삭제완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)