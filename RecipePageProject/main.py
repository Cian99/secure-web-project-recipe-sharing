# import necessary packages
import os
from flask import Flask, render_template, request, url_for, flash, session
from werkzeug.utils import redirect, secure_filename
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, current_user, logout_user, login_required

db_file = "mySQLite.db"

# define upload folder - database will store the path to the file (images of the recipes)
UPLOAD_FOLDER = 'static/uploads'
# specify allowed upload type
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# specify maximum file size - 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024

# setup flask application
app = Flask(__name__)
app.config['ENV'] = "Development"
app.config['DEBUG'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create a Bcrypt object
bcrypt = Bcrypt (app)

# Create a LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'loginAction'

# Create a User Class for the user that will be stored when the user is logged in
class User():
    def __init__(self, username):
        self.username = username
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return self.username

# Define a userloader function
@login_manager.user_loader
def load_user(username):
    return User(username)

# Set a secret key for the login session
app.secret_key = 'super secret key'

# set session timeout - 30minutes (1800s)
app.permanent_session_lifetime = 1800

# set default page
@app.route('/')
def index():
    return redirect(url_for('login'))

# direct to signup html page
@app.route('/signup')
def signup():
    if (current_user.is_authenticated):
        flash("You are already logged in!")
        return redirect(url_for('profile'))
    return render_template("signup.html")

# complete new user creation
@app.route('/signupAction', methods=['POST'])
def signupAction():
    username=""
    password=""
    email=""
    fname=""
    lname =""
    if request.form.get("username"):
        username=request.form.get("username")
    if request.form.get("password"):
        password = request.form.get("password")
        # HASHING PASSWORD
        # password is a normal string, we need to hash it before put in database
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        print("True Password:", password, ", Hashed Password:", hashed_password)
        password = hashed_password
    if request.form.get("email"):
        email = request.form.get("email")
    if request.form.get("fname"):
        fname = request.form.get("fname")
    if request.form.get("lname"):
        lname = request.form.get("lname")

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        # PARAMETERIZATION - get user inputs as parameters (prevent SQL injection attack)
        myquery="INSERT INTO USER (Username, Password, Email, First_Name, Last_Name) VALUES (?, ?, ?, ?, ?)"
        print("My query is: ", myquery)
        cursor.execute(myquery, (username, password, email, fname, lname))
        conn.commit()

        # if this works, this means the user has been added succesfully
        # we then send them to the login page

    except Error as e:
        # if the user is not added, we will get an exception which will be caught here
        # tell user signup has failed and send them to the sign up page again
        flash("Failled to signup. Try again!")
        return redirect(url_for('signup'))
    finally:
        if conn:
            conn.close()
    flash("Account created successfully.")
    return redirect(url_for('login'))

# direct to login html
@app.route('/login')
def login():
    # If user is already logged in we need to redirect them to their profile
    if (current_user.is_authenticated):
        flash("You are already logged in.")
        return redirect(url_for('profile'))
    return render_template("login.html")

# complete login action
@app.route('/loginAction', methods=['POST'])
def loginAction():
    username=""
    password=""
    if request.form.get("username"):
        username=request.form.get("username")
    if request.form.get("password"):
        password = request.form.get("password")
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        # PARAMETERIZATION
        myquery="SELECT Password FROM USER WHERE Username=?"
        data=cursor.execute(myquery, (username,))
        passwordInDB=None
        for row in data:
            passwordInDB=row[0]
        if passwordInDB:
            # We have found a username matching the one provide for the login
            # Now, we need to check that the password provide for the login is also correct
            validPassword = bcrypt.check_password_hash(passwordInDB, password)

            # AUTHENTICATION
            # If the passwords match, we need to mark them as logged in and send them to their profile
            # Else we need to send them to the login page again
            if validPassword:
                login_user(User(username))
                flash("You are now logged in.")
                return redirect(url_for('profile'))
            else:
                # The password does not match
                # we need to send them to the login page again
                flash("Your username or password are incorrect! Try to login again.")
                return redirect(url_for('login'))
            pass
        else:
            # The Username does not exist
            # we need to send them to the login page again
            flash("Your username is incorrect! Try to login again. Or create an account")
            return redirect(url_for('login'))
    except Error as e:
        # if there was an error in the login, we will get an exception which will be caught here
        # So we need to send the user to the login page again
        flash("Failled to login. Try again!")
        return redirect(url_for('login'))
    finally:
        if conn:
            conn.close()
    flash("You are now logged in.")
    return redirect(url_for('profile'))

# user session should be logged out after 30 minutes on inactivity

# user details to display on profile page
@app.route('/profile', methods=['GET'])
def profile():
    # If the user is not logged in, we need to redirect them to the login page
    if not (current_user.is_authenticated):
        flash("You need to login to access the profile page.")
        return redirect(url_for('login'))

    # If the user is logged in, we need to get their username
    myusername = current_user.username

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Get the personal data of the user
        myquery = "SELECT Email, First_Name, Last_Name, FavouriteRecipes FROM USER WHERE Username=?"
        cursor.execute(myquery, (myusername,))
        user_data = cursor.fetchone()

        if user_data:
            myemail = user_data[0]
            myfname = user_data[1]
            mylname = user_data[2]
            favourite_recipe_ids = user_data[3].split(",") if user_data[3] else []

            # Fetch the details of favorite recipes using recipe IDs
            favourite_recipes = []
            for recipe_id in favourite_recipe_ids:
                cursor.execute("SELECT * FROM RECIPE WHERE ID=?", (recipe_id,))
                recipe_data = cursor.fetchone()
                if recipe_data:
                    favourite_recipes.append(recipe_data)
        else:
            return render_template("error.html", message="User data not found.")

    except Error as e:
        print(e)
        return render_template("error.html", message="Database error.")

    finally:
        if conn:
            conn.close()

    return render_template("profile.html", username=myusername, email=myemail, fname=myfname, lname=mylname,
                           favourite_recipes=favourite_recipes)

# direct to add recipe page
@app.route('/addRecipe')
def addRecipe():
    if not(current_user.is_authenticated):
        flash("You need to login to add recipes.")
        return redirect(url_for('login'))
    return render_template("addRecipe.html")

# complete add recipe action
@app.route('/addRecipeAction', methods=['POST'])
def addRecipeAction():
    # get parameters from the form
    recipeName = request.form.get("recipeName")
    info = request.form.get("info")
    time = request.form.get("time")
    steps = request.form.get("steps")
    image = request.files.get("image")

    # checks
    if not (current_user.is_authenticated):
        flash("You need to login to add recipes.")
        return redirect(url_for('login'))

    if not (recipeName and info and time and steps):
        flash("Please fill out all required fields.")
        return redirect(url_for('addRecipe'))

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Check if the recipe name already exists for the user
        query = "SELECT * FROM RECIPE WHERE Username = ? AND RecipeName = ?"
        cursor.execute(query, (current_user.username, recipeName))
        existing_recipe = cursor.fetchone()

        if existing_recipe:
            flash("Recipe with the same name already exists.")
            return redirect(url_for('addRecipe'))

        # FILE UPLOAD SECURITY
        # Check if the file has an allowed extension
        if image and '.' in image.filename and image.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
            flash("File type not allowed. Please upload an image with extensions: png, jpg, jpeg.")
            return redirect(url_for('addRecipe'))

        # Check if the file size exceeds the maximum allowed size
        if image and len(image.stream.read()) > MAX_FILE_SIZE:
            flash("File size exceeds the maximum allowed size (5MB).")
            return redirect(url_for('addRecipe'))

        # Reset the file pointer to the beginning of the file then save image
        image.stream.seek(0)

        # Save the uploaded image
        if image:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image.filename))
            image.save(image_path)
        else:
            image_path = None

        # Insert the recipe into the database
        query = "INSERT INTO RECIPE (Username, RecipeName, Info, Time, Steps, ImagePath) VALUES (?, ?, ?, ?, ?, ?)"
        cursor.execute(query, (current_user.username, recipeName, info, time, steps, image_path))
        conn.commit()

        flash("Recipe added successfully.")
        return redirect(url_for('profile'))

    except Error as e:
        print(e)
        flash("Failed to add recipe. Please try again.")
        return redirect(url_for('addRecipe'))

    finally:
        if conn:
            conn.close()

# direct and display all recipes by a user
@app.route('/userRecipes')
def userRecipes():
    if not (current_user.is_authenticated):
        flash("You need to login to view user recipes.")
        return redirect(url_for('login'))

    # If the user is logged in, we need to get their username
    myusername = current_user.username

    conn = None
    userRecipes = []
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Get the personal data of the user
        myquery = "SELECT * FROM RECIPE WHERE Username=?"
        cursor.execute(myquery, (myusername,))
        recipe_data = cursor.fetchall()

        if recipe_data:
            for row in recipe_data:
                myrecipeID = row[0]
                myrecipeName = row[2]
                myrecipeInfo = row[3]
                myrecipeTime = row[4]
                myrecipeImgPath = row[5]
                myrecipeSteps = row[6]
                userRecipes.append({
                    'id': myrecipeID,
                    'name': myrecipeName,
                    'info': myrecipeInfo,
                    'time': myrecipeTime,
                    'img_path': myrecipeImgPath,
                    'steps': myrecipeSteps
                })

        else:
            flash("No recipes found for the current user.")

    except Error as e:
        print(e)
        return render_template("error.html", message="Database error.")

    finally:
        if conn:
            conn.close()

    return render_template("userRecipes.html", username=myusername, userRecipes=userRecipes)

# allow user to delete one of their own recipes
@app.route('/deleteRecipe', methods=['POST'])
def deleteRecipe():
    if not current_user.is_authenticated:
        flash("You need to login to delete recipes.")
        return redirect(url_for('login'))

    # Get the recipe ID to delete
    recipe_id = request.form.get("recipe_id")

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Check if the recipe exists
        query = "SELECT COUNT(*) FROM RECIPE WHERE ID = ?"
        cursor.execute(query, (recipe_id,))
        recipe_exists = cursor.fetchone()[0]

        if not recipe_exists:
            flash("Recipe does not exist.")
            return redirect(url_for('userRecipes'))

        # Delete the recipe from the database
        delete_query = "DELETE FROM RECIPE WHERE ID = ?"
        cursor.execute(delete_query, (recipe_id,))
        conn.commit()

        # Remove the recipe from users' favorite recipes
        # First, get all users who have this recipe in their favorites
        user_query = "SELECT Username, FavouriteRecipes FROM USER WHERE FavouriteRecipes LIKE ?"
        cursor.execute(user_query, ('%' + recipe_id + '%',))
        users_with_recipe = cursor.fetchall()

        # Update each user's favorite recipes list
        for user in users_with_recipe:
            username = user[0]
            favorite_recipes = user[1].split(',')
            favorite_recipes.remove(recipe_id)
            updated_favorites = ','.join(favorite_recipes)

            update_query = "UPDATE USER SET FavouriteRecipes = ? WHERE Username = ?"
            cursor.execute(update_query, (updated_favorites, username))

        conn.commit()

        flash("Recipe deleted successfully.")
        return redirect(url_for('userRecipes'))

    except Error as e:
        print(e)
        flash("Failed to delete recipe.")
        return redirect(url_for('userRecipes'))

    finally:
        if conn:
            conn.close()

# direct to recipe search
@app.route('/searchRecipe')
def searchRecipe():
    if not (current_user.is_authenticated):
        flash("You need to login to search recipes.")
        return redirect(url_for('login'))
    return render_template("searchRecipe.html")

# complete recipe search by keyword
@app.route('/searchRecipeAction', methods=['POST'])
def searchRecipeAction():
    # get the keyword from the form
    keyword = request.form.get("keyword")
    if not keyword:
        flash("Please enter a keyword to search.")
        return redirect(url_for('searchRecipe'))

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        try:
            # find recipes in the database that contain keyword
            query = "SELECT * FROM RECIPE WHERE RecipeName LIKE ?"
            cursor.execute(query, ('%' + keyword + '%',))
            recipes = cursor.fetchall()

            if not recipes:
                flash("No recipes found with the given keyword.")
                return redirect(url_for('searchRecipe'))

            # return the results
            return render_template("searchResult.html", keyword=keyword, recipes=recipes)

        except Error as e:
            # Handle any potential database errors here
            flash("Failed to retrieve recipes from the database. Please try again.")
            return redirect(url_for('searchRecipe'))

    except Error as e:
        print(e)
        flash("Failed to search for recipes. Please try again.")
        return redirect(url_for('searchRecipe'))

    finally:
        if conn:
            conn.close()

# direct to search for a user portfolio
@app.route('/searchPortfolio')
def searchPortfolio():
    if not (current_user.is_authenticated):
        flash("You need to login to search users.")
        return redirect(url_for('login'))
    return render_template("searchPortfolio.html")

# take username and show their work
@app.route('/searchPortfolioAction', methods=['POST'])
def searchPortfolioAction():
    # get from the form
    user = request.form.get("user")
    if not user:
        flash("Please enter a user to search.")
        return redirect(url_for('searchPortfolio'))

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM RECIPE WHERE Username=?"
            cursor.execute(query, (user,))
            portfolio = cursor.fetchall()

            # needs to be valid username that has recipes associated
            if not portfolio:
                flash("No recipes found with the given username.")
                return redirect(url_for('searchPortfolio'))

            return render_template("searchResultPortfolio.html", username=user, portfolio=portfolio)

        except Error as e:
            # Handle any potential database errors here
            flash("Failed to retrieve recipes from the database. Please try again.")
            return redirect(url_for('searchPortfolio'))

    except Error as e:
        print(e)
        flash("Failed to search for user. Please try again.")
        return redirect(url_for('searchPortfolio'))

    finally:
        if conn:
            conn.close()

# add recipe to the users favourites
@app.route('/addToFavourites', methods=['POST'])
def addToFavourites():
    if not current_user.is_authenticated:
        flash("You need to login to add recipes to favourites.")
        return redirect(url_for('login'))

    # get the recipe ID
    recipe_id = request.form.get("recipe_id")

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Check if the recipe exists
        query = "SELECT COUNT(*) FROM RECIPE WHERE ID = ?"
        cursor.execute(query, (recipe_id,))
        recipe_exists = cursor.fetchone()[0]

        if not recipe_exists:
            flash("Recipe does not exist.")
            return redirect(url_for('searchRecipe'))

        # Get the current user's favourite recipes
        query = "SELECT FavouriteRecipes FROM USER WHERE Username = ?"
        cursor.execute(query, (current_user.username,))
        current_favourites = cursor.fetchone()[0]

        # check if the recipe is already in the user's favourites
        if current_favourites and recipe_id in current_favourites.split(','):
            flash("Recipe is already in your favorites.")
            return redirect(request.referrer, code=307)

        # Append the new recipe ID to the list of favourites
        if current_favourites:
            current_favourites += ',' + recipe_id
        else:
            current_favourites = recipe_id

        # Update the FavouriteRecipes column
        update_query = "UPDATE USER SET FavouriteRecipes = ? WHERE Username = ?"
        cursor.execute(update_query, (current_favourites, current_user.username))
        conn.commit()

        flash("Recipe added to favourites successfully.")
        # do not want redirect after every added favourite
        # return redirect(url_for('profile'))
        # redirect back to same page before form submission
        # code=307 indicates to browser preserve the request method during redirection
        # This should resolve the "Method Not Allowed" error
        return redirect(request.referrer, code=307)

    except Error as e:
        print(e)
        flash("Failed to add recipe to favourites.")
        return redirect(url_for('profile'))

    finally:
        if conn:
            conn.close()

# remove a recipe from the users favourites
@app.route('/removeFromFavourites', methods=['POST'])
def removeFromFavourites():
    if not current_user.is_authenticated:
        flash("You need to login to manage your favourite recipes.")
        return redirect(url_for('login'))

    recipe_id = request.form.get("recipe_id")

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Check if the recipe ID exists in the user's favourites
        query = "SELECT FavouriteRecipes FROM USER WHERE Username = ?"
        cursor.execute(query, (current_user.username,))
        row = cursor.fetchone()
        if not row:
            flash("Failed to remove recipe from favourites. User not found.")
            return redirect(url_for('profile'))

        favourite_recipes = row[0]
        if favourite_recipes is None:
            flash("Failed to remove recipe from favourites. User has no favourite recipes.")
            return redirect(url_for('profile'))

        # Split the string of favourite recipe IDs and remove the selected ID
        recipe_ids = favourite_recipes.split(',')
        if recipe_id in recipe_ids:
            recipe_ids.remove(recipe_id)

        # Update the user's favourite recipes in the database
        updated_favourite_recipes = ','.join(recipe_ids)
        update_query = "UPDATE USER SET FavouriteRecipes = ? WHERE Username = ?"
        cursor.execute(update_query, (updated_favourite_recipes, current_user.username))
        conn.commit()

        flash("Recipe removed from favourites successfully.")
        return redirect(url_for('profile'))

    except Error as e:
        print(e)
        flash("Failed to remove recipe from favourites. Please try again.")
        return redirect(url_for('profile'))

    finally:
        if conn:
            conn.close()

# logout out the user
@app.route("/logout")
def logout():
    # If the user is logged in, then logout the user
    if current_user.is_authenticated:
        logout_user()
    flash("Logout successfull.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
