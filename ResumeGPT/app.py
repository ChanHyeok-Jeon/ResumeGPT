import os
from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
from werkzeug.utils import secure_filename
import mysql.connector

from gpt.chat_engine import ask_with_resume, ask_with_jobseeker_list
from gpt.summarizer import extract_text_from_bytes

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='0000',
        database='project',
        auth_plugin='mysql_native_password'
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form['id']
    password = request.form['password']
    user_type = request.form['user_type']
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if user_type == 'jobseeker':
            cursor.execute("SELECT * FROM jobseeker WHERE id = %s AND password = %s", (user_id, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['user_type'] = 'jobseeker'
                session['user_name'] = user['name']
                return redirect(url_for('chat_jobseeker'))
        elif user_type == 'employer':
            cursor.execute("SELECT * FROM employer WHERE id = %s AND password = %s", (user_id, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['user_type'] = 'employer'
                session['user_name'] = user['name']
                return redirect(url_for('chat_employer'))

        # 로그인 실패 시 오류 메시지와 함께 login.html 다시 렌더링
        return render_template('login.html', error='회원정보가 잘못되었습니다.')
    except mysql.connector.Error as err:
        return f"DB 오류: {err}"
    finally:
        cursor.close()
        conn.close()

@app.route('/chat_jobseeker')
def chat_jobseeker():
    if 'user_id' in session and session.get('user_type') == 'jobseeker':
        return render_template('chat_jobseeker.html', name=session['user_name'])
    return redirect(url_for('home'))

@app.route('/chat_employer')
def chat_employer():
    if 'user_id' in session and session.get('user_type') == 'employer':
        return render_template('chat_employer.html', name=session['user_name'])
    return redirect(url_for('home'))

@app.route('/register_jobseeker', methods=['GET', 'POST'])
def register_jobseeker():
    if request.method == 'POST':
        name = request.form['name']
        user_id = request.form['id']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        resume_file = request.files.get('resume')
        resume_data = None
        if resume_file and resume_file.filename.endswith('.pdf'):
            resume_data = resume_file.read()
        else:
            return "PDF 이력서를 업로드해주세요."
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = "INSERT INTO jobseeker (id, name, password, email, phone, resume) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (user_id, name, password, email, phone, resume_data))
            conn.commit()
            return redirect(url_for('home'))
        except mysql.connector.Error as err:
            return f"DB 오류: {err}"
        finally:
            cursor.close()
            conn.close()
    return render_template('register_jobseeker.html')

@app.route('/register_employer', methods=['GET', 'POST'])
def register_employer():
    if request.method == 'POST':
        name = request.form['name']
        user_id = request.form['id']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        photo = request.files.get('photo')
        image_url = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(filepath)
            image_url = f"/{filepath.replace(os.sep, '/')}"
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = "INSERT INTO employer (id, name, password, email, phone, image_url) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (user_id, name, password, email, phone, image_url))
            conn.commit()
            return redirect(url_for('home'))
        except mysql.connector.Error as err:
            return f"DB 오류: {err}"
        finally:
            cursor.close()
            conn.close()
    return render_template('register_employer.html')

@app.route('/download_resume/<user_id>')
def download_resume(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT resume FROM jobseeker WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            return Response(
                result[0],
                mimetype='application/pdf',
                headers={"Content-Disposition": f"attachment; filename={user_id}_resume.pdf"}
            )
        else:
            return "이력서가 없습니다."
    except Exception as e:
        return f"오류 발생: {e}"
    finally:
        cursor.close()
        conn.close()

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()

        if not user_input:
            return jsonify({'response': '❗ 메시지를 입력해주세요.'}), 400

        user_type = session.get('user_type')
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if user_type == 'jobseeker':
            cursor.execute("SELECT resume FROM jobseeker WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            if result and result['resume']:
                resume_text = extract_text_from_bytes(result['resume'])
                gpt_response = ask_with_resume(resume_text, user_input)
                return jsonify({'response': gpt_response})
            else:
                return jsonify({'response': '❗ 이력서가 존재하지 않습니다.'})

        elif user_type == 'employer':
            cursor.execute("SELECT name, resume FROM jobseeker")
            jobseekers = cursor.fetchall()

            jobseeker_infos = []
            for js in jobseekers:
                if js['resume']:
                    text = extract_text_from_bytes(js['resume'])
                    jobseeker_infos.append({
                        "name": js['name'],
                        "text": text[:1000]  # 너무 길면 자름
                    })

            gpt_response = ask_with_jobseeker_list(jobseeker_infos, user_input)
            return jsonify({'response': gpt_response})

        else:
            return jsonify({'response': '⚠️ 알 수 없는 사용자 유형입니다.'})

    except Exception as e:
        return jsonify({'response': f'[서버 오류] {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/find_id')
def find_id():
    return render_template('find_id.html')

@app.route('/find_password')
def find_password():
    return render_template('find_password.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_type', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
