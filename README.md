# Secure Web Project - Recipe Realm

Recipe Realm is a visually appealing platform where food enthusiasts can share their culinary creations, explore new recipes, and save their favorites. Users can upload detailed recipes, search for new ones, and manage their personal recipe collection—all while enjoying a secure, user-friendly experience.

## Objective
This project was developed as part of an educational module. The website satisfies the following requirements:
- User authentication
- At least 3 pages to capture user input and insert data into a database
- At least 3 pages to retrieve and display data from the database
- A search function that returns user input and results
- Use of SQLite for database management
- Implementation of several security features, including authentication, session management, input validation, and more.

## Features
This website includes a variety of security features to safeguard user data and maintain the integrity of the website, they include:
- **Authentication**: Users must provide a username and password to log in. Passwords are securely hashed.
- **Form Validation**: Ensures all fields are filled, reducing incomplete data.
- **Session Management**: User sessions persist until manual logout or 30 minutes of inactivity.
- **Parametrized Queries**: Prevent SQL injection by using safe query practices.
- **XSS Prevention**: Special characters are escaped to prevent Cross-Site Scripting.
- **File Upload Security**: Users can upload only specific image types with a size limit of 5MB to prevent DOS attacks.

## Design Flow
Upon entering the website, users are greeted with a visually appealing interface and prompted to log in or create an account.

- **Profile Page**: Shows user details and favorite recipes. Links are available to view personal contributions, add new recipes, search recipes, search users, and logout.
- **Recipe Contributions**: Displays the user's uploaded recipes, with an option to delete any of them.
- **Add a Recipe**: Users can add a new recipe by providing the recipe name, ingredients, time, steps, and an image. Validation ensures image types and size restrictions are met.
- **Search for a Recipe**: Users can search for recipes by keyword. Matching recipes can be added to the user's favorites.
- **Search for a User**: Users can search by username to view all recipes from a particular user.
- **Logout**: Users can log out manually, or sessions will expire after 30 minutes of inactivity.

## Frameworks and Languages
- **HTML, CSS, JavaScript**: Frontend design and interactivity.
- **Flask**: Backend framework that handles routing, templates, and sessions.
- **Python**: Server-side programming language for the project.
- **SQLite**: Lightweight relational database to store user and recipe information.
- **SQL**: Query language used to interact with the SQLite database.

## Setup Instructions
1. Clone the repository: `git clone https://github.com/Cian99/secure-web-project-recipe-sharing.git`
2. Install the required packages: `pip install -r requirements.txt`
3. Run the Flask app: `python main.py`
4. Navigate to `http://127.0.0.1:5000/` in your web browser.