import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
import chardet
import zipfile



# Connect to SQLite database or create if not exists
DATABASE_FILE = "users.db"
conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()

# Create Users table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   username TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE ,
                   password TEXT NOT NULL)''')
conn.commit()

# Create Files table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS files
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   user_id INTEGER,
                   filename TEXT NOT NULL,
                   FOREIGN KEY(user_id) REFERENCES users(id))''')
conn.commit()

# Helper function to get binary file downloader
def get_binary_file_downloader(file_path, file_name):
    with open(file_path, 'rb') as f:
        data = f.read()
    base64_encoded = base64.b64encode(data).decode()
    download_link = f'<a href="data:application/octet-stream;base64,{base64_encoded}" download="{file_name}">Click here to download</a>'
    st.markdown(download_link, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="File Upload App", page_icon=":floppy_disk:")
    st.title("File Upload App")

    menu = ["Home", "Signup", "Login", "Review Analysis"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Welcome to the Review Analysis App")

    elif choice == "Signup":
        sign_up()

    elif choice == "Login":
        login()

    elif choice == "Review Analysis":
        review_analysis()

       


# Streamlit login page
def login():
    st.subheader("Login")

    username_email = st.text_input("Username or Email")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        user = authenticate_user(username_email, password)
        if user:
            st.success("Login Successful!")
            st.balloons()
            st.session_state["user"] = user["username"]
            st.session_state["user_id"] = user["id"]
        else:
            st.error("Invalid Login Credentials")

# Rest of the code remains unchanged



# Streamlit signup page
def sign_up():
    st.subheader("Sign Up")

    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    sign_up_button = st.button("Sign Up")

    if sign_up_button:
        if password == confirm_password:
            if not user_exists(username, email):
                create_user(username, email, password)
                st.success("Account created successfully! Please login.")
            else:
                st.error("Username or Email already exists. Please choose a different one.")
        else:
            st.error("Passwords do not match.")




# Streamlit user dashboard
def review_analysis():
    st.subheader("Review Analysis")

    user = st.session_state.get("user")
    user_id = st.session_state.get("user_id")



    if not user or not user_id:
        st.warning("Please log in to access the review analysis.")
        return

    st.write(f"Welcome, {user}!")

   
    # Add a menu to choose different options
    menu_options = ["Upload File", "Previously Uploaded Files"]
    selected_option = st.selectbox("Select an option:", menu_options)
    uploaded_file = None  # Initialize uploaded_file outside of the conditionals


    open_button_key = "open_uploaded_file"
    if selected_option == "Upload File":
        uploaded_file = st.file_uploader("Upload a file", type=["txt", "csv", "xlsx"])
        if uploaded_file:
            save_uploaded_file(user, uploaded_file)

            # Display the uploaded file details
            st.subheader("Uploaded File Details:")
            st.write(f"File Name: {uploaded_file.name}")
            st.write(f"File Type: {uploaded_file.type}")
            st.write(f"File Size: {len(uploaded_file.getvalue())} bytes")

        user_files = []  # Initialize user_files with an empty list
 
            
          # Download button for the uploaded file
    
        download_button_key = "download_uploaded_file"
        open_button_key = "open_uploaded_file"
       

# Button to open the uploaded file (only rendered when uploaded_file is not None)
    open_button_clicked = st.button("Open Uploaded File", key=open_button_key) if uploaded_file else False

    if open_button_clicked:
     try:
        file_type = None

        if uploaded_file.type == "application/vnd.ms-excel" or uploaded_file.name.endswith(('.xls', '.xlsx')):
            file_type = "excel"
        elif uploaded_file.type == "text/plain" or uploaded_file.name.endswith('.txt'):
            file_type = "txt"
        elif uploaded_file.type == "text/csv" or uploaded_file.name.endswith(('.csv', '.tsv')):
            file_type = "csv"

        if file_type is not None:
            if file_type == "excel":
                df = pd.read_excel(uploaded_file)
                st.subheader("Content of Uploaded Excel File:")
            elif file_type == "txt":
                df = pd.read_csv(uploaded_file, delimiter='\t' if uploaded_file.name.endswith('.tsv') else None)
                st.subheader("Content of Uploaded Text File:")
            elif file_type == "csv":
                df = pd.read_csv(uploaded_file)
                st.subheader("Content of Uploaded CSV File:")

            st.write(df)
        else:
            st.error("Unsupported file format. Please upload a txt, CSV, or Excel file.")

     except pd.errors.ParserError as e:
            st.error(f"Unable to parse the file. Exception details: {str(e)}. Please choose a different file or encoding.")

     st.markdown("---")


# Check if uploaded_file is not None before accessing its attributes
    if uploaded_file:
            # Define file_path based on the user and file name
            file_path = os.path.join("uploads", user, uploaded_file.name)

            if st.button("Download Uploaded File", key=download_button_key):
                get_binary_file_downloader(file_path, uploaded_file.name)

            st.markdown("---")

# Display previously uploaded files
    elif selected_option == "Previously Uploaded Files":
     user_files = get_user_files(user_id)

    if user_files:
        st.subheader("Previously Uploaded Files")
        displayed_files = set()  # Keep track of displayed files to avoid duplicates
        for index, file in enumerate(user_files):
            file_path = os.path.join("uploads", user, file)

            # Check if the file has already been displayed
            if file not in displayed_files:
                st.markdown(f"File: {file}")

                open_button_key = f"open_button_{file}_{index}"
                if st.button(f"Open {file}", key=open_button_key):
                    try:
                        file_extension = file.split('.')[-1].lower()
                        if file_extension in ['xls', 'xlsx']:
                            df = pd.read_excel(file_path, engine='openpyxl')
                            st.subheader(f"Content of {file} (Excel):")
                            st.write(df)
                        elif file_extension in ['csv', 'txt']:
                            df = pd.read_csv(file_path, encoding='latin-1')
                            st.subheader(f"Content of {file} (CSV or TXT):")
                            st.write(df)
                        else:
                            st.error(f"Unsupported file format: {file_extension}")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")

                download_button_key = f"download_button_{file}_{index}"
                if st.button(f"Download {file}", key=download_button_key):
                    # Download the file
                    get_binary_file_downloader(file_path, file)

                # Add the file to the set of displayed files
                displayed_files.add(file)

        st.markdown("---")
   # Add logout option to the sidebar
    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.session_state["user_id"] = None
        st.success("Logout Successful!")

        # Trigger a rerun of the Streamlit app to redirect the user
        st.experimental_rerun()
    
# Helper function to authenticate user
def authenticate_user(username_email, password):
    # Check if the username_email contains "@" to determine if it's an email
    if "@" in username_email:
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (username_email, password))
    else:
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username_email, password))

    user_data = cursor.fetchone()

    if user_data:
        user = {"id": user_data[0], "username": user_data[1], "password": user_data[2]}
        return user
    else:
        return None


# Helper function to get user ID
def get_user_id(username):
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = cursor.fetchone()
    return user_id[0] if user_id else None

# Helper function to check if user exists
def user_exists(username, email=None):
    if email:
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
    else:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

    return cursor.fetchone() is not None


# Helper function to create a new user
def create_user(username, email, password):
    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
    conn.commit()


# Helper function to save uploaded file
def save_uploaded_file(username, uploaded_file):
    user_id = get_user_id(username)
    if user_id:
        cursor.execute("INSERT INTO files (user_id, filename) VALUES (?, ?)", (user_id, uploaded_file.name))
        conn.commit()

        user_dir = os.path.join("uploads", username)
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

# Helper function to get user's uploaded files
def get_user_files(user_id):
    cursor.execute("SELECT filename FROM files WHERE user_id = ?", (user_id,))
    files = cursor.fetchall()
    return [file[0] for file in files]

if __name__ == "__main__":
   main()