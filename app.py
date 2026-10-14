from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature


app = Flask(__name__)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "wajidpro131@gmail.com"
app.config["MAIL_PASSWORD"] = "whts fowc gzus zdzc"

mail = Mail(app)

app.secret_key = "employee-secret-key"




def get_db_connection():

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="employeedb"
    )

    return conn




@app.route("/")
def home():

    return render_template("home.html")


@app.route("/about")
def about():

    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        msg = Message(
            subject="Employee Management System - Contact",
            sender=app.config["MAIL_USERNAME"],
            recipients=[app.config["MAIL_USERNAME"]]
        )

        msg.body = f"""
Name: {name}

Email: {email}

Message:
{message}
"""

        mail.send(msg)

        return render_template(
            "contact.html",
            success="Your message has been sent successfully."
        )

    return render_template("contact.html")




@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check passwords
        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match"
            )

        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)

        try:
            # Check whether username or email already exists
            query = """
                SELECT username, email
                FROM users
                WHERE username = %s OR email = %s
            """

            cursor.execute(query, (username, email))
            existing_user = cursor.fetchone()

            if existing_user:
                return render_template(
                    "register.html",
                    error="Username or email already exists"
                )

            # Insert new user
            query = """
                INSERT INTO users (username, email, password)
                VALUES (%s, %s, %s)
            """

            cursor.execute(
                query,
                (username, email, password)
            )

            conn.commit()

            return redirect(url_for("login"))

        except mysql.connector.Error as e:
            conn.rollback()
            app.logger.exception("Registration database error")

            return render_template(
                "register.html",
                error="Registration failed. Please try again."
            )

        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]


        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)


        query = """
        SELECT * FROM users
        WHERE username = %s
        """

        cursor.execute(query, (username,))

        user = cursor.fetchone()


        cursor.close()

        conn.close()


        if user and user["password"] == password:

            session["logged_in"] = True

            session["user_id"] = user["user_id"]

            session["username"] = user["username"]


            return redirect(url_for("dashboard"))


        return render_template(
            "login.html",
            error="Invalid username or password"
        )


    return render_template("login.html")



@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))


    return render_template(
        "dashboard.html"
    )



@app.route("/add-employee", methods=["GET", "POST"])
def add_employee():

    if "user_id" not in session:

        return redirect(url_for("login"))


    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        phone = request.form["phone"]

        age = request.form["age"]

        department = request.form["department"]


        conn = get_db_connection()

        cursor = conn.cursor()


        query = """
        INSERT INTO employees
        (name, email, phone, age, department, user_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """


        values = (
            name,
            email,
            phone,
            age,
            department,
            session["user_id"]
        )


        cursor.execute(query, values)

        conn.commit()


        cursor.close()

        conn.close()


        return redirect(
            url_for("view_employees")
        )


    return render_template(
        "add_employee.html"
    )


@app.route("/view-employees")
def view_employees():

    if "user_id" not in session:

        return redirect(url_for("login"))


    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)


    query = """
    SELECT *
    FROM employees
    WHERE user_id = %s
    ORDER BY employee_id
    """


    cursor.execute(
        query,
        (session["user_id"],)
    )


    employees = cursor.fetchall()


    cursor.close()

    conn.close()


    return render_template(
        "view_employees.html",
        employees=employees
    )


@app.route("/edit-employee/<int:id>", methods=["GET", "POST"])
def edit_employee(id):

    if "user_id" not in session:

        return redirect(url_for("login"))


    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)


    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        phone = request.form["phone"]

        age = request.form["age"]

        department = request.form["department"]


        query = """
        UPDATE employees

        SET
            name = %s,
            email = %s,
            phone = %s,
            age = %s,
            department = %s

        WHERE employee_id = %s
        AND user_id = %s
        """


        values = (
            name,
            email,
            phone,
            age,
            department,
            id,
            session["user_id"]
        )


        cursor.execute(query, values)

        conn.commit()


        cursor.close()

        conn.close()


        return redirect(
            url_for("view_employees")
        )


    query = """
    SELECT *
    FROM employees
    WHERE employee_id = %s
    AND user_id = %s
    """


    cursor.execute(
        query,
        (id, session["user_id"])
    )


    employee = cursor.fetchone()


    cursor.close()

    conn.close()


    return render_template(
        "edit_employee.html",
        employee=employee
    )




@app.route("/delete-employee/<int:id>")
def delete_employee(id):

    if "user_id" not in session:

        return redirect(url_for("login"))


    conn = get_db_connection()

    cursor = conn.cursor()


    query = """
    DELETE FROM employees
    WHERE employee_id = %s
    AND user_id = %s
    """


    cursor.execute(
        query,
        (id, session["user_id"])
    )


    conn.commit()


    cursor.close()

    conn.close()


    return redirect(
        url_for("view_employees")
    )




@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )
    


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"].strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT email FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        message = (
            "If this email is registered, "
            "a password reset link will be sent."
        )

        if user:

            serializer = URLSafeTimedSerializer(app.secret_key)

            token = serializer.dumps(
                email,
                salt="password-reset"
            )

            reset_link = url_for(
                "reset_password",
                token=token,
                _external=True
            )

            msg = Message(
                subject="Employee Password Reset",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email]
            )

            msg.body = (
                "Click the link below to reset your password:\n\n"
                + reset_link
                + "\n\nThis link expires in 30 minutes."
            )

            try:
                mail.send(msg)
            except Exception:
                app.logger.exception("Failed to send reset email")

        return render_template(
            "forgot_password.html",
            message=message
        )

    return render_template("forgot_password.html")



@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    serializer = URLSafeTimedSerializer(app.secret_key)

    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=1800
        )
    except SignatureExpired:
        return render_template(
            "reset_password.html",
            error="Reset link expired. Request a new link."
        )
    except BadSignature:
        return render_template(
            "reset_password.html",
            error="Invalid reset link. Request a new link."
        )

    if request.method == "POST":

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not password:
            return render_template(
                "reset_password.html",
                error="Password cannot be empty."
            )

        if password != confirm_password:
            return render_template(
                "reset_password.html",
                error="Passwords do not match."
            )

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET password = %s WHERE email = %s",
            (password, email)
        )

        conn.commit()
        updated = cursor.rowcount

        cursor.close()
        conn.close()

        if updated == 0:
            return render_template(
                "reset_password.html",
                error="Unable to reset password for this account."
            )

        return redirect(url_for("login"))

    return render_template("reset_password.html")



if __name__ == "__main__":

    app.run(debug=True)
    



