from flask import Flask,render_template,request,flash,url_for,session,redirect
from otp import genotp 
from cmail import sendmail
import mysql.connector
from adminmail import adminsendmail
from adminotp import adotp
import os
import razorpay
RAZORPAY_KEY_ID='rzp_test_YxFqNpnySKudsR'
RAZORPAY_KEY_SECRET='Tjpe9IjAW2WBuOvlCUQ9xNUN'
client=razorpay.Client(auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET))
from itemid import itemidotp
mydb=mysql.connector.connect(host='localhost',
user='root',
password='admin',
db='ecomerce'
)
app=Flask(__name__)
app.secret_key='jnvnkdfjvndjs'
@app.route('/')
def base():
    return render_template('welcome.html')
@app.route('/reg',methods=['GET','POST'])
def register():
    if request.method=="POST":
        username=request.form['username']
        mobile=request.form['mobile']
        email=request.form['email']
        address=request.form['address']
        password=request.form['password']
        cursor=mydb.cursor()
        cursor.execute('select email from signup')
        data=cursor.fetchall()
        cursor.execute('select mobile from signup')
        edata=cursor.fetchall()
        if(mobile,)in edata:
            flash('User already exist')
            return render_template('register.html')
        if(email,)in data:
            flash('Email address already exists')
            return render_template('register.html')
        cursor.close() 
        otp=genotp()
        subject='thanks for registering to the application'
        body=f'use this otp to register {otp}'
        sendmail(email,subject,body)
        return render_template('otp.html',otp=otp,username=username,mobile=mobile,email=email,address=address,password=password)
    else:
        return render_template('register.html')
@app.route('/otp/<otp>/<username>/<mobile>/<email>/<address>/<password>',methods=['GET','POST'])
def otp(otp,username,mobile,email,address,password):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mydb.cursor()
            lst=[username,mobile,email,address,password]
            query='insert into signup values(%s,%s,%s,%s,%s)'
            cursor.execute(query,lst)
            mydb.commit()
            cursor.close()
            flash('Details registered')
            return redirect('login')
        else:
            flash('Wrong otp')
            return render_template('otp.html',otp=otp,username=username,mobile=mobile,email=email,address=address,password=password)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor()
        cursor.execute('select count(*) from signup where username=%s and \
        password=%s',[username,password])
        count=cursor.fetchone()[0]
        print(count)
        if count==0:
            flash('Invalid email or password')
            return render_template('login.html')
        else:
            session['user']=username
            if not session.get(username):
                session[username]={}
            return redirect(url_for('home1'))
    return render_template('login.html')
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home1'))
    else:
        flash('already logged out!')
        return redirect(url_for('login'))
'''admin login code'''
@app.route('/adminsignup',methods=['GET','POST'])
def adminsignup():
    if request.method=='POST':
        name=request.form['name']
        mobile=request.form['mobile']
        email=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor()
        cursor.execute('select email from adminsignup')
        data=cursor.fetchall()
        cursor.execute('select mobile from adminsignup')
        edata=cursor.fetchall()
        #print(data)
        if (mobile, ) in edata:
            flash('User already exisit')
            return render_template('adminsignup.html')
        if (email, ) in data:
            flash('Email id already exisit')
            return render_template('adminsignup.html')
        cursor.close()
        adminotp=adotp()
        subject='thanks for registering to the application'
        body=f'use this adminotp to register {adminotp}'
        sendmail(email,subject,body)
        return render_template('adminotp.html',adminotp=adminotp,name=name,mobile=mobile,email=email,password=password)
    else:
        return render_template('adminsignup.html')    
@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if session.get('admin'):
        return redirect(url_for('adminhome'))
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor()
        cursor.execute('select count(*) from adminsignup where email=%s and password=%s',[email,password])
        count=cursor.fetchone()[0]
        print(count)
        if count==0:
            flash('Invalid email or password')
            return render_template('adminlogin.html')
        else:
            session['admin']=email
            return redirect(url_for('adminhome'))
    return render_template('adminlogin.html')
@app.route('/adminhome')
def adminhome():
    if session.get('admin'):
        return render_template('admindashboard.html')
    else:
        #flash('login first')
        return redirect(url_for('adminlogin'))
@app.route('/adminlogout')
def adminlogout():
    if session.get('admin'):
        session.pop('admin')
        return redirect(url_for('adminlogin'))
    else:
        flash('already logged out!')
        return redirect(url_for('adminlogin'))
@app.route('/adminotp/<adminotp>/<name>/<mobile>/<email>/<password>',methods=['GET','POST'])
def adminotp(adminotp,name,mobile,email,password):
    if request.method=='POST':
        uotp=request.form['adminotp']
        if adminotp==uotp:
            cursor=mydb.cursor()
            lst=[name,mobile,email,password]
            query='insert into adminsignup values(%s,%s,%s,%s)'
            cursor.execute(query,lst)
            mydb.commit()
            cursor.close()
            flash('Details registered')
            return redirect(url_for('adminlogin'))
        else:
            flash('Wrong otp')
            return render_template('adminotp.html',adminotp=adminotp,name=name,mobile=mobile,email=email,password=password)

@app.route('/additems',methods=['GET','POST'])
def additems():
    if session.get('admin'):
        if request.method=="POST":
            name=request.form['name']
            discription=request.form['desc']
            quantity=request.form['qty']
            category=request.form['category']
            price=request.form['price']
            image=request.files['image']
            valid_categories=['electronics','grocery','fashion','home']
            if category not in valid_categories:
                flash('Invalid category.Please select a valid option.')
                return render_template('items.html')
            cursor=mydb.cursor()
            idotp=itemidotp()
            filename=idotp+'.jpg'
            cursor.execute('insert into additems(itemid,name,discription,qty,category,price)\
            values(%s,%s,%s,%s,%s,%s)',[idotp,name,discription,quantity,category,price])
            mydb.commit()
            path=os.path.dirname(os.path.abspath(__file__))
            static_path=os.path.join(path,'static')
            image.save(os.path.join(static_path,filename))
            flash('Item added successfuly!')
        return render_template('items.html')
    else:
        return redirect(url_for('adminlogin'))
@app.route('/homepage')
def home1():
    
    return render_template('homepage.html')
@app.route('/dashboardpage')
def dashboardpage():
    cursor=mydb.cursor()
    cursor.execute('select *from additems')
    items=cursor.fetchall()
    print(items)
    return render_template('dashboard.html',items=items)
@app.route('/status')
def status():
    cursor=mydb.cursor()
    cursor.execute('select * from additems')
    items=cursor.fetchall()
    return render_template('status.html',items=items)
@app.route('/updateproducts/<itemid>',methods=['GET','POST'])
def updateproducts(itemid):
    if session.get('admin'):
        print(itemid)
        cursor=mydb.cursor()
        cursor.execute('select name,discription,qty,category,price from additems \
        where itemid=%s',[itemid])
        items=cursor.fetchone()
        print(items)
        cursor.close()
        if request.method=="POST":
            name=request.form['name']
            discription=request.form['desc']
            quantity=request.form['qty']
            category=request.form['category']
            price=request.form['price']
            cursor=mydb.cursor()
            cursor.execute('update additems set name=%s,discription=%s,qty=%s,category=%s\
            ,price=%s where itemid=%s',[name,discription,quantity,category,price,itemid])
            mydb.commit()
            cursor.close()
            return redirect(url_for('adminhome'))
        return render_template('updateproducts.html',items=items)
    else:
        return redirect(url_for('adminlogin'))

@app.route('/deleteproducts/<itemid>')
def deleteproducts(itemid):
    cursor=mydb.cursor()
    cursor.execute('delete from additems where itemid=%s',[itemid])
    mydb.commit()
    cursor.close()
    path=os.path.dirname(os.path.abspath(__file__))
    static_path=os.path.join(path,'static')
    filename=itemid+'.jpg'
    os.remove(os.path.join(static_path,filename))
    flash('deleted')
    return redirect(url_for('status'))
@app.route('/index')
def index():
    cursor = mydb.cursor(buffered=True)
    # Fetching item details from the database
    cursor.execute('SELECT itemid, name, qty, category, price FROM additems')
    item_data = cursor.fetchall()
    print(item_data)  # Debugging to verify data
    return render_template('index.html', item_data=item_data)

@app.route('/addcart/<itemid>/<name>/<category>/<price>/<quantity>',methods=['GET','POST'])
def addcart(itemid,name,category,price,quantity):
    if not session.get('user'):
        return redirect(url_for('login'))
    else:
        print(session)
        if itemid not in session.get(session['user'],{}):
            if session.get(session['user']) is None:
                session[session['user']]={}
            session[session['user']][itemid]=[name,price,1,f'{itemid}.jpg',category]
            session.modified=True
            flash(f'{name} added to cart')
            return redirect(url_for('addedsuccess'))
        session[session['user']][itemid][2]+=1
        session.modified=True
        flash(f'{name} quantity increased in the cart')
        return redirect(url_for('addedsuccess'))
@app.route('/addedsucess')
def addedsuccess():
    return render_template('addedsucess.html')
@app.route('/viewcart')
def viewcart():
    if not session.get('user'):
        return redirect(url_for('login'))
    user_cart=session.get(session.get('user'))#retrive the cart items from the session
    if not user_cart:
        items='empty'
    else:
        items=user_cart     #fetch the items from the session
    if items=='empty':
        return '<h3> Your cart is empty</h3>'
    return render_template('cart.html',items=items)
@app.route('/cartpop/<itemid>')
def cartpop(itemid):
    print(itemid)
    if session.get('user'):
        #print(session)
        session[session.get('user')].pop(itemid)
        session.modified=True
        flash('item removed')
        #print(session)
        return redirect(url_for('viewcart'))
    else:
        return redirect(url_for('login'))
@app.route('/dis/<itemid>')
def dis(itemid):
    cursor=mydb.cursor()
    cursor.execute('select *from additems where itemid=%s',[itemid])
    items=cursor.fetchone()
    return render_template('discription.html',items=items)
@app.route('/category/<category>',methods=['GET','POST'])
def category(category):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select *from additems where category=%s',[category])
        data=cursor.fetchall()
        cursor.close()
        return render_template('categories.html',data=data)
    else:
        return redirect( url_for('login'))

@app.route('/pay/<itemid>/<name>/<int:price>', methods=['POST'])
def pay(itemid, name, price):
    try:
        # Get the quantity from the form
        qty = int(request.form['qyt'])

        # Calculate the total amount in paise (price is in rupees)
        total_price = int(price) * qty  # Ensure integer multiplication

        print(f"Creating payment for Item ID: {itemid}, Name: {name}, Total Price: {total_price}")

        # Create Razorpay order
        order = client.order.create({
            'amount': total_price,
            'currency': 'INR',
            'payment_capture': '1'
        })

        print(f"Order created: {order}")
        return render_template('pay.html', order=order, itemid=itemid, name=name, price=total_price, qty=qty)
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return str(e), 400
@app.route('/success', methods=['POST'])
def success():
    if session.get('user'):
        
        payment_id = request.form.get('razorpay_payment_id')
        order_id = request.form.get('razorpay_order_id')
        signature = request.form.get('razorpay_signature')
        name = request.form.get('name')
        itemid = request.form.get('itemid')
        total_price = request.form.get('total_price')
        qyt = request.form.get('qyt')

        # Validate qyt
        if not qyt or not qyt.isdigit():
            flash("Invalid quantity provided!")
            return "Invalid quantity", 400

        qyt = int(qyt)  # Convert to integer

        # Verification process
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        try:
            client.utility.verify_payment_signature(params_dict)
            cursor = mydb.cursor(buffered=True)
            cursor.execute(
                'INSERT INTO orders(itemid, item_name, total_price, user, qty) VALUES (%s, %s, %s, %s, %s)',
                [itemid, name, total_price, session.get('user'), qyt]
            )
            mydb.commit()
            cursor.close()
            flash('Order placed successfully')
            return redirect(url_for('orders'))
        except razorpay.errors.SignatureVerificationError:
            return 'Payment verification failed!', 400
    else:
        return redirect(url_for('login'))
@app.route('/orders')
def orders():
    if session.get('user'):
        user=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select *from orders where user=%s',[user])
        data=cursor.fetchall()
        cursor.close()
        return render_template('orderdisplay.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        if not name or not email or not message:
            flash("All fields are required!", "error")
            return redirect(url_for('contact'))
        
        # Here, handle form data (e.g., store in a database, send email)
        flash("Thank you for reaching out! We will get back to you soon.", "success")
        return redirect(url_for('contact'))
    
    return render_template('contact.html')  

@app.route('/search',methods=['GET','POST'])
def search():
    if request.method=='POST':
        name=request.form['search']
        print(name)
        cursor=mydb.cursor()
        cursor.execute('select *from additems where name=%s',[name])
        data=cursor.fetchall()
        return render_template('dashboard.html',items=data)
if __name__ == '__main__':
    app.run(debug=True)