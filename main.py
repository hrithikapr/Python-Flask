#--------------------Importing Libraries-------------------------
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
# from flask_mail import Mail
import json
import os
import math
from datetime import datetime

#--------open json file-----------
with open('config.json', 'r') as c:
    param = json.load(c)['params']
#------------assign template folder to your app variable-----------
local_server = True
app = Flask(__name__, template_folder='template')
app.secret_key = 'super-secret-key'   #----------sign in variable-------
app.config['UPLOAD_FOLDER'] = param['upload_location'] #------file uploading location----------
# app.config.update(
#     MAIL_SERVER = 'smtp.gmail.com',
#     MAIL_PORT = '465',
#     MAIL_USE_SSL = True,
#     MAIL_USERNAME = param['gmail_user'],
#     MAIL_PASSWORD = param['gmail_password']
# )
# mail = Mail(app)

#----configuring database using Sqlalchemy---------------
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = param['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = param['prod_uri']

db = SQLAlchemy(app)

#------------variables that will asiign values in database of caontact-----------------
class Contacts(db.Model):
    # SNo, Name, Email, Phone_num, Msg, Date
    Sno = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.String(20),  nullable=False)
    Phone_num = db.Column(db.String(20), nullable=False)
    Msg = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(50), nullable=False)

#------------variables that will asiign values in database of Posts-----------------
class Posts(db.Model):
    # SNo, Slug, Title, Content, Date
    Sno = db.Column(db.Integer, primary_key=True)
    Slug = db.Column(db.String(21), nullable=False)
    Title = db.Column(db.String(20),  nullable=False)
    Tag_line = db.Column(db.String(20),  nullable=False)
    Content = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(50), nullable=False)
    Img_file = db.Column(db.String(50), nullable=False)


#----At home page----------
@app.route("/")
def home():

#-----------pagination fr Next & Previous pages-----------
    posts = Posts.query.filter_by().all()#[0:param['no_of_posts']]
    last = math.ceil(len(posts)/int(param['no_of_posts']))
    # Pagination Logic
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(param['no_of_posts']): (page-1)*int(param['no_of_posts']) + int(param['no_of_posts']) ]
    # First -> prev = #, # next = page+1
    if (page==1):
        prev = '#'
        next = '/?page='+ str(page+1)
    # Last -> prev = page-1, next = #
    elif (page == last):
        prev = '/?page='+ str(page-1)
        next = '#'
    # Middle -> prev  page-1, next = page+1
    else:
        prev = '/?page='+ str(page-1)
        next = '/?page='+ str(page+1)
    
    return render_template('index.html', params=param, posts=posts, prev=prev, next=next)

#--------about page------------
@app.route('/about')
def about():
    return render_template('about.html', params=param)

#-------dashboard page-------------
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
#---------user is already logged in------------------
    if ('user' in session and session['user'] == param['admin_user']):
        post = Posts.query.all()
        return render_template('dashboard.html', params=param, posts=post)
#---------user is not logged in------------------
    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == param['admin_user'] and userpass == param['admin_password']):
            # SET THE SESSION VARIABLE
            session['user'] = username
            post = Posts.query.all()
            return render_template('dashboard.html', params=param, posts=post)

    return render_template('signIn.html', params=param)

#-------edit page-------------------
@app.route('/edit/<string:sno>', methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == param['admin_user']):
        if(request.method == 'POST'):
    #-------variable to store data from html page------------
            box_title = request.form.get('title')
            box_tline = request.form.get('tline')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            box_img_file = request.form.get('img_file')
            box_date = datetime.now()
    #------if we want to add ner post------------
            if sno == '0':
                post = Posts(Title=box_title, Slug=box_slug, Tag_line=box_tline, Content=box_content, Img_file=box_img_file, Date=box_date)
                db.session.add(post)
                db.session.commit()
    #---------if we want t edit post-----------
            else:
                post = Posts.query.filter_by(Sno=sno).first()
                post.Title = box_title
                post.Slug = box_slug
                post.Tag_line = box_tline
                post.Content = box_content
                post.Img_file = box_img_file
                post.Date = box_date        
                db.session.commit()
                return redirect('/edit/'+sno)

        post = Posts.query.filter_by(Sno=sno).first()
        return render_template('edit.html', params=param, post=post, Sno=sno)

#-----------uploader page-----------
@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == param['admin_user']):
        if (request.method == 'POST'):
        #------variable to store type of file from html page---------
            f = request.files['file1']
        #------store the file in specified folder--------
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully..."

#-----------logout page----------
@app.route("/logout")
def logout():
#-----return the user in dashboard----------
    session.pop('user')
    return redirect('/dashboard')

#--------delete the post--------
@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == param['admin_user']):
        post = Posts.query.filter_by(Sno=sno).first()
    #------delete the specified post using delete buttom-------
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')
#-----contact page---------
@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
#---------fetch data from html table-------------
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        msg=request.form.get('msg')
#---------Add Entry to the database-------------
        entry = Contacts(Name=name, Email=email, Phone_num=phone, Msg=msg, Date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('New message from ' + name, sender=email, recipients=[param['gmail_user']], body=msg + "\n" + phone)

    return render_template('contact.html', params=param)

#-----signin page-----------
@app.route("/signin")
def signin():
    return render_template('signIn.html', params=param)

#------adding slug---------
@app.route('/post/<string:post_slug>', methods=['GET'])
def post_rout(post_slug):
    post =  Posts.query.filter_by(Slug=post_slug).first()
    return render_template('post.html', params=param, posts=post)

#-------adding bootstrap in html-------
@app.route('/bootstrap')
def bootstrap():
    return render_template('bootstrap.html')
#----auto run after saving---------
app.run(debug=True)