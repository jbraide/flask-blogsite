from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from functools import wraps


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please Login','danger')
            return redirect(url_for('login'))
    return wrap

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Joseph4all_'
app.config['MYSQL_DB'] = 'blogapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# initialize mysql
mysql = MySQL(app)



@app.route('/')
def index():
    # create cursor
    cur = mysql.connection.cursor()

    #execute

    result = cur.execute('SELECT * FROM posts')

    posts = cur.fetchall()

    if result > 0:
        return render_template('index.html', posts=posts)
    else:
        msg = 'No Posts Found'
        return render_template('index.html', msg=msg )
    return render_template('index.html')

class BlogPost(Form):
    title = StringField('Title',[validators.Length(min=1, max=200)])
    subtitle = StringField('Subtitle', [validators.Length(min=1,max=200)])
    author = StringField('Author', [validators.Length(min=1, max= 100)])
    body = TextAreaField('Body', [validators.Length(min=30)])


@app.route('/add', methods=['GET','POST'])
@is_logged_in
def add():
    form = BlogPost(request.form)

    if request.method == 'POST' and form.validate():
        title = form.title.data
        subtitle = form.subtitle.data
        author = form.subtitle.data
        body = form.body.data

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO posts (title, subtitle, author, body) VALUES(%s,%s, %s, %s)", (title, subtitle, author, body))

        mysql.connection.commit()

        cur.close()

        return redirect(url_for('index'))

    return render_template('add.html',form=form)

@app.route('/about')
def about():

    return render_template('about.html')

@app.route('/post/<string:id>')
def posts(id):

    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM posts where id=%s", [id])

    post = cur.fetchone()

    return render_template('post.html', post=post)

@app.route('/edit/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM posts WHERE id=%s", [id])

    post = cur.fetchone()

    form = BlogPost(request.form)

    #populate post form fields
    form.title.data = post['title']
    form.subtitle.data = post['subtitle']
    form.author.data = post['author']
    form.body.data = post['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        subtitle = request.form['subtitle']
        author = request.form['author']
        body = request.form['body']

        cur = mysql.connection.cursor()

        cur.execute("UPDATE posts SET title=%s, subtitle=%s, author=%s, body=%s WHERE id=%s",[title,subtitle, author, body, id])

        mysql.connection.commit()

        cur.close()

        return redirect(url_for('dashboard'))
    return render_template('edit.html',form=form)


@app.route('/delete/<string:id>', methods=['POST'])
@is_logged_in
def delete(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM posts WHERE id=%s", [id])

    mysql.connection.commit()

    cur.close()

    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM posts ")

    posts = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html',posts=posts)
    else:
        msg= 'No posts found'
        return render_template('dashboard.html', msg=msg)
    cur.close()


# administrator

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username',[validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
    validators.DataRequired(),
    validators.EqualTo('confrm', message = 'Passwords do not match ')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO admin_users (name,email,username, password) VALUES(%s,%s,%s,%s)", (name,email,username,password))

        mysql.connection.commit()

        cur.close()

        return redirect(url_for('login'))
    return render_template('register.html', form=form )

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method== 'POST':
        username = request.form['username']
        password_candidate = request.form['password']


        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM admin_users WHERE username=%s", [username])

        if result > 0:
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(password_candidate, password):

                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('dashboard'))

            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)

                cur.close()
        else:
            error = "username not found"
            return render_template('login.html', error=error)
    return render_template('login.html')


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    return redirect(url_for('login'))



if __name__ ==  '__main__':
    app.secret_key = 'secret1234'
    app.run(debug=True)
