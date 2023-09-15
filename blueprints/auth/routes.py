from flask import Blueprint,render_template,redirect,url_for,flash,request
from flask_login import login_user,logout_user,login_required,current_user
from sqlalchemy import select

from ...models import bcrypt,db,Users
from ...forms import LoginForm,RegisterForm


auth = Blueprint('auth',__name__,template_folder='auth_templates')

@auth.route('/login', methods = ['POST','GET'])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in")
        return redirect(url_for('site.account'))
    form = LoginForm()
    if request.method == 'POST':
        user_data = db.session.execute(select(Users).where(Users.username == form.username.data))
        user = (user_data.freeze().data)
        if len(user) < 1:
            flash("Username not found")
            # render_template('login.html',form=form)
        else:
            if form.validate_on_submit():
                password = form.password.data
                pwd = user[0].password
            
                if user != None:
                    if bcrypt.check_password_hash(pwd, password) == True:
                        user[0].authenticated = True
                        db.session.add(user[0])
                        db.session.commit()
                        login_user(user[0], remember=True)
                        flash('Logged in successfully.')
                        next = request.args.get('next')
                        return redirect(next or url_for('site.account'))
                    else: 
                        flash('Incorrect Password')
                        return render_template("login.html",form=form)
                else: 
                    flash("User not found")
                    return render_template("login.html",form=form)   
                  
    return render_template("login.html",form=form)

@auth.route("/logout", methods=['GET','POST'])
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    flash("Logged out successfully")
    return redirect("/login")

@auth.route('/register', methods = ['POST','GET'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        usrname = form.username.data
        eml = form.email.data
        username_check = (db.session.execute(select(Users).where(Users.username==usrname))).freeze().data
        email_check = (db.session.execute(select(Users).where(eml==Users.email))).freeze().data
        if len(email_check) > 0:
            flash('This email address is already in use', category='error')
        elif len(username_check) > 0:
            flash('This username is already in use, please try again', category='error')
        else:
            hpwd = Users.pass_hash(form.password.data)
            new_user = Users(username=usrname,email=eml,password=hpwd)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('register.html',form=form)
