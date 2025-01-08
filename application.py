from flask import Flask, render_template, request, flash, url_for, session, redirect
from otp import genotp 
from cmail import sendmail
import mysql.connector
from adminmail import adminsendmail
from adminotp import adotp
import os
import razorpay
from itemid import itemidotp

RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_YxFqNpnySKudsR')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'Tjpe9IjAW2WBuOvlCUQ9xNUN')
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

db = os.environ['RDS_DB_NAME']
user = os.environ['RDS_USERNAME']
password = os.environ['RDS_PASSWORD']
host = os.environ['RDS_HOSTNAME']
port = os.environ['RDS_PORT']

# Database connection setup
mydb = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=db
)

cursor = mydb.cursor(buffered=True)
# Create tables if not exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS signup (
        username VARCHAR(30) DEFAULT NULL,
        mobile VARCHAR(12) DEFAULT NULL,
        email VARCHAR(50) NOT NULL,
        address VARCHAR(75) DEFAULT NULL,
        password TEXT,
        PRIMARY KEY (email),
        UNIQUE KEY unique_email (email)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS adminsignup (
        name VARCHAR(30) DEFAULT NULL,
        mobile BIGINT NOT NULL,
        email VARCHAR(50) DEFAULT NULL,
        password VARCHAR(40) DEFAULT NULL,
        PRIMARY KEY (mobile),
        UNIQUE KEY email (email)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS additems (
        itemid VARCHAR(30) NOT NULL,
        name VARCHAR(30) DEFAULT NULL,
        discription LONGTEXT,
        qty VARCHAR(20) DEFAULT NULL,
        category ENUM('electronics', 'grocery', 'fashion', 'home') DEFAULT NULL,
        price VARCHAR(30) DEFAULT NULL,
        PRIMARY KEY (itemid)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id BIGINT NOT NULL AUTO_INCREMENT,
        itemid VARCHAR(30) NOT NULL,
        item_name LONGTEXT NOT NULL,
        qty INT DEFAULT NULL,
        total_price BIGINT DEFAULT NULL,
        user VARCHAR(100) DEFAULT NULL,
        PRIMARY KEY (order_id),
        FOREIGN KEY (user) REFERENCES signup(username),
        FOREIGN KEY (itemid) REFERENCES additems(itemid)
    )
""")

cursor.close()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def base():
    return render_template('welcome.html')

@app.route('/reg', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        mobile = request.form['mobile']
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']

        cursor = mydb.cursor()
        cursor.execute('SELECT email FROM signup')
        data = cursor.fetchall()
        cursor.execute('SELECT mobile FROM signup')
        edata = cursor.fetchall()

        if (mobile,) in edata:
            flash('User already exists')
            return render_template('register.html')

        if (email,) in data:
            flash('Email address already exists')
            return render_template('register.html')

        cursor.close()
        otp = genotp()
        subject = 'Thanks for registering to the application'
        body = f'Use this OTP to register: {otp}'
        sendmail(email, subject, body)

        return render_template('otp.html', otp=otp, username=username, mobile=mobile, email=email, address=address, password=password)

    return render_template('register.html')

@app.route('/otp/<otp>/<username>/<mobile>/<email>/<address>/<password>', methods=['GET', 'POST'])
def otp(otp, username, mobile, email, address, password):
    if request.method == 'POST':
        uotp = request.form['otp']
        if otp == uotp:
            cursor = mydb.cursor()
            lst = [username, mobile, email, address, password]
            query = 'INSERT INTO signup VALUES(%s, %s, %s, %s, %s)'
            cursor.execute(query, lst)
            mydb.commit()
            cursor.close()
            flash('Details registered')
            return redirect(url_for('login'))
        else:
            flash('Wrong OTP')
            return render_template('otp.html', otp=otp, username=username, mobile=mobile, email=email, address=address, password=password)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        cursor = mydb.cursor()
        cursor.execute('SELECT COUNT(*) FROM signup WHERE username=%s AND password=%s', [username, password])
        count = cursor.fetchone()[0]
        cursor.close()

        if count == 0:
            flash('Invalid username or password')
            return render_template('login.html')

        session['user'] = username
        return redirect(url_for('home1'))

    return render_template('login.html')

# Other route handlers...

if __name__ == '__main__':
    app.run(debug=True)
