from flask import Blueprint,render_template,request,redirect,flash,url_for
from sqlalchemy import select,text,delete
from flask_login import current_user,login_required

from ...models import db,Property,Expenses,Income,Users
from ...forms import AddPropertyForm,IncomeForm,AddImageForm,ExpenseForm
from ...helper import calc_roi

site=Blueprint('site',__name__,template_folder='site_templates')


@site.route('/', methods = ['POST','GET'])
def index():
    return render_template('index.html')


@site.route('/contact', methods = ['POST','GET'])
def contact():
    return render_template('contact.html')

@site.route('/account', methods = ['POST','GET'])
def account():
    return render_template('my_account.html')

@site.route('/properties', methods = ['POST','GET'])
def properties():
    prop_data= db.session.execute(text(f'SELECT * FROM property WHERE _user_id = {current_user.user_id}'))
    prop_count = len(prop_data.all())
    if prop_count < 1:
        return render_template('my_properties.html', no_properties=True)
    
    prop_data= db.session.execute(text(f'SELECT * FROM property WHERE _user_id = {current_user.user_id}'))
    properties = prop_data.all()
    return render_template('my_properties.html',properties=properties)


@site.route('/add-edit', methods = ['POST','GET'])
def add_edit():
    form = AddPropertyForm()  
    if form.validate_on_submit():
        address = form.address.data
        purchase = form.purch_price.data
        est_rent = form.est_rent.data
        purchase_price = form.purch_price.data
        new_property=Property(address=address,purch_price=purchase,est_rent=est_rent,_user_id=current_user.user_id)
        db.session.add(new_property)
        db.session.commit()
        prop_id_q = db.session.execute(select(Property.prop_id).where(Property.address == address))
        prop_id = prop_id_q.all()[0][0]
        expense_amount = purchase_price
        expense_name = "Purchase Price"
        new_expense=Expenses(name=expense_name,amount=expense_amount,prop_id=prop_id,user_id=current_user.user_id)
        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('site.properties'))
    
    return render_template('add_edit_property.html',form=form)


@site.route('/view-exp-inc',defaults={'id':0}, methods = ['POST','GET'])
@site.route('/view-exp-inc/<id>', methods = ['POST','GET'])
@login_required

def view_exp_inc(id):
    prop_data=db.session.execute(select(Property).join(Users).filter(Users.user_id==current_user.user_id).filter(Property.prop_id==id))
    property = [data[0] for data in prop_data]
    income_data = db.session.execute(select(Income).join(Property).filter(Income.prop_id == id))
    expense_data = db.session.execute(select(Expenses).join(Property).filter(Expenses.prop_id == id))
    incomes=(income_data.freeze().data)
    expenses=(expense_data.freeze().data)
    if len(incomes) < 1 and len(expenses) < 1:
        no_monies=True
        return render_template('inc_exp_view.html', no_monies=no_monies,property=property,id=id)
    else:
        income_sum=0
        for income in incomes:
            income_sum+=income.amount      
        expense_sum=0
        for expense in expenses:
            expense_sum+=expense.amount

        return render_template('inc_exp_view.html',incomes=incomes,expenses=expenses,property=property,expense_sum=expense_sum,income_sum=income_sum,id=id)
    
@site.route('/Income',defaults={'id':0},methods=['POST','GET'])
@site.route('/Income/<id>',methods=['POST','GET'])
@login_required
def add_inc(id):
    prop = db.session.execute(select(Property).where(Property.prop_id==id))
    props=list(map(list, prop))
    address = props[0][0].address
    form = IncomeForm()
    if request.method=="POST" and form.validate_on_submit():
        prop_id = id
        income_amount = form.income_amt.data
        income_name = form.income_name.data

        new_income=Income(name=income_name,amount=income_amount,prop_id=id,user_id=current_user.user_id)
        db.session.add(new_income)
        db.session.commit()

        exp_total = db.session.execute(text(f'select sum(amount) from expense inner join property on property.prop_id = expense.prop_id where expense.user_id = {current_user.user_id}'))
        inc_total = db.session.execute(text(f'select sum(amount) from income inner join property on property.prop_id = income.prop_id where income.user_id = {current_user.user_id}'))
        roi= calc_roi(props[0][0].purch_price,exp_total.all()[0][0],inc_total.all()[0][0])
        roif = "%.2f" % roi
        query=text(f'UPDATE property SET roi = {roif} WHERE property.prop_id = {prop_id}')
        db.session.execute(query)
        db.session.commit()
        return redirect('/properties')
    
    return render_template('add_income.html',form=form,id=id,address=address)

@site.route('/Expense',defaults={'id':0},methods=['POST','GET'])
@site.route('/Expense/<id>',methods=['POST','GET'])
@login_required
def add_exp(id):
    prop = db.session.execute(select(Property).where(Property.prop_id==id))
    address = prop.freeze().data[0].address
    form = ExpenseForm()
    if request.method=="POST" and form.validate_on_submit():
        prop_id = id
        expense_amount = form.expense_amt.data
        expense_name = form.expense_name.data
        new_expense=Expenses(name=expense_name,amount=expense_amount,prop_id=id,user_id=current_user.user_id)
        db.session.add(new_expense)
        db.session.commit()
        return redirect('/properties')
    
    return render_template('add_expense.html',form=form,id=id,address=address)

@site.route('/Add-Image/<prop_id>',methods=['GET','POST'])
@login_required
def add_image(prop_id):
    form=AddImageForm()
    if form.validate_on_submit():
        img_url = form.imageURL.data
        #### This looks like the safer and more acceptable way to add/update ####
        _user_id = current_user.user_id
        query = text('UPDATE property SET image = :img_url WHERE property.prop_id = :prop_id AND property._user_id = :_user_id')
        db.session.execute(query, {"img_url": img_url, "prop_id": prop_id, "_user_id": current_user.user_id})
        db.session.commit()
        return redirect('/properties')
    
    return render_template('add_image.html',form=form,prop_id=prop_id)

@site.route('/delete/<id>', methods=['POST','GET'])
@login_required
def prop_delete(id):
    db.session.execute(delete(Property).where(Property.prop_id == id))
    db.session.commit()
    return redirect('/properties')

@site.route('/delete-expense/<inc_id>',methods=['GET','POST'])
@login_required
def del_exp(inc_id):
    db.session.execute(text(f'DELETE FROM expense WHERE expense.inc_id = {inc_id}'))
    db.session.commit()
    return redirect('/properties')

@site.route('/delete-income/<inc_id>',methods=['GET','POST'])
@login_required
def del_inc(inc_id):
    db.session.execute(text(f'DELETE FROM income WHERE income.inc_id = {inc_id}'))
    db.session.commit()
    return redirect('/properties')