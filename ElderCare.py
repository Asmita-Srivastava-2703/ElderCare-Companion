import tkinter as tk
from tkinter import messagebox, font, scrolledtext
import customtkinter as ctk
from customtkinter import CTkImage,CTk, CTkLabel
from PIL import Image, ImageTk,ImageDraw, ImageOps
from tkinter import font
import sqlite3
import random
import string
import nltk
import subprocess
import sys
import os
import time
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from newspaper import Article
import warnings
import webbrowser
import hangman

warnings.filterwarnings('ignore')
nltk.download('punkt', quiet=True)

conn = sqlite3.connect('user_data.db')
connD = sqlite3.connect('disease_data.db')

# Create a cursor object to interact with the database
cursor = conn.cursor()
cursorD = connD.cursor()
# Create a table with name, age, phone, email, and password if it doesn't already exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_data (
    name TEXT PRIMARY KEY,
    age INTEGER,
    phone TEXT,
    email TEXT,
    password TEXT
)
''')
# Ensure that the diseases table is created before inserting data
cursorD.execute('''
CREATE TABLE IF NOT EXISTS disease_data (
    disease TEXT PRIMARY KEY,
    article_link TEXT
)
''')

# Commit the changes to ensure the table creation is successful
connD.commit()

# Insert disease data (only if not already present)
diseases = [
    ('kidney', 'https://www.mayoclinic.org/diseases-conditions/chronic-kidney-disease/symptoms-causes/syc-20354521'),
    ('hypertension', 'https://en.wikipedia.org/wiki/Hypertension'),
    ('arthritis', 'https://en.wikipedia.org/wiki/Arthritis'),
    ('diabetes', 'https://en.wikipedia.org/wiki/Diabetes'),
    ('stroke', 'https://en.wikipedia.org/wiki/Stroke')
]

# Insert each disease only if it doesn't already exist
for disease, link in diseases:
    cursorD.execute('''
    INSERT OR IGNORE INTO disease_data (disease, article_link)
    VALUES (?, ?)
    ''', (disease, link))

# Commit the changes to the diseases table
connD.commit()



conn.commit()


# Sample insert for testing purposes (Uncomment for first-time use)
# cursor.execute("INSERT INTO diseases (disease, article_link) VALUES (?, ?)", 
#               ('chronic kidney disease', 'https://www.mayoclinic.org/diseases-conditions/chronic-kidney-disease/symptoms-causes/syc-20354521'))
# conn.commit()

# Helper function to fetch article content for a given disease
def fetch_article(disease_name):
    cursorD.execute("SELECT article_link FROM disease_data WHERE disease = ?", (disease_name.lower(),))
    result = cursorD.fetchone()
    if result:
        article_link = result[0]
        article = Article(article_link)
        article.download()
        article.parse()
        return article.text
    else:
        return None


# Prepare punctuation removal dictionary and normalization function
remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)
def LemNormalize(text):
    return nltk.word_tokenize(text.lower().translate(remove_punct_dict))

# Greeting function
def greeting(sentence):
    GREETING_INPUTS = ["hi", "hello", "hola", "greetings", "what's up", "wassup", "hey", "hey how are you doing?"]
    GREETING_RESPONSES = ["howdy", "hi", "hey", "what's good?", "hello", "hey there"]
    for word in sentence.split():
        if word.lower() in GREETING_INPUTS:
            return random.choice(GREETING_RESPONSES)

# DOC Bot window for disease-based article retrieval and Q&A
def DocBot():
    botWindow = tk.Toplevel()
    botWindow.geometry("500x800")
    botWindow.title("Doc Bot")


    chat_area = scrolledtext.ScrolledText(botWindow, wrap=tk.WORD, width=60, height=25, state='disabled')
    chat_area.pack(pady=10)

    # Disease selection and response handling
    def load_disease():
        disease_name = disease_entry.get().strip()
        if not disease_name:
            messagebox.showerror("Input Error", "Please enter a disease name.")
            return

        article_content = fetch_article(disease_name)
        if article_content:
            global sent_tokens
            sent_tokens = nltk.sent_tokenize(article_content)
            chat_area.config(state='normal')
            chat_area.insert(tk.END, f"DOC Bot: Loaded article for '{disease_name}'. You can ask me questions about it.\n")
            chat_area.config(state='disabled')
        else:
            chat_area.config(state='normal')
            chat_area.insert(tk.END, "DOC Bot: Sorry, I couldn't find any information on that disease.\n")
            chat_area.config(state='disabled')

    def bot_response(user_response):
        sent_tokens.append(user_response)
        TfidfVec = TfidfVectorizer(tokenizer=LemNormalize, stop_words='english')
        tfidf = TfidfVec.fit_transform(sent_tokens)
        vals = cosine_similarity(tfidf[-1], tfidf)
        idx = vals.argsort()[0][-2]
        flat = vals.flatten()
        flat.sort()
        score = flat[-2]

        if score == 0:
            response = "I apologize, I do not understand."
        else:
            response = sent_tokens[idx]

        sent_tokens.remove(user_response)
        return response

    # Function to handle user input and bot response
    def ask_question():
        user_response = user_entry.get().strip()
        if user_response.lower() == 'bye':
            chat_area.config(state='normal')
            chat_area.insert(tk.END, "DOC Bot: Goodbye!\n")
            chat_area.config(state='disabled')
            return
        if user_response:
            chat_area.config(state='normal')
            chat_area.insert(tk.END, f"You: {user_response}\n")
            chat_area.insert(tk.END, f"DOC Bot: {bot_response(user_response)}\n")
            chat_area.config(state='disabled')
        user_entry.delete(0, tk.END)

    # Set up disease name entry
    disease_label = tk.Label(botWindow, text="Enter Disease Name: ", font=("Helvetica", 14))
    disease_label.pack(pady=10)
    disease_entry = tk.Entry(botWindow, font=("Helvetica", 14), width=40)
    disease_entry.pack(pady=5)

    load_button = tk.Button(botWindow, text="Load Disease Info", font=("Helvetica", 14), command=load_disease)
    load_button.pack(pady=10)

    user_label = tk.Label(botWindow, text="Ask a Question: ", font=("Helvetica", 14))
    user_label.pack(pady=10)
    user_entry = tk.Entry(botWindow, font=("Helvetica", 14), width=40)
    user_entry.pack(pady=5)

    ask_button = tk.Button(botWindow, text="Ask", font=("Helvetica", 14), command=ask_question)
    ask_button.pack(pady=10)

    botWindow.mainloop()

# Create main login page
def LoginPage():
    loginWindow = ctk.CTkToplevel()
    loginWindow.geometry("550x700")
    loginWindow.title("User Details Form")

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Main Frame
    main_frame = ctk.CTkFrame(loginWindow, fg_color="#DCDCEC", corner_radius=10)
    main_frame.pack(pady=20, padx=20, fill="both", expand=True)

    # Title Label
    title_label = ctk.CTkLabel(main_frame, text="Enter Your Details:", font=("Comic Sans MS", 18, "italic"))
    title_label.pack(pady=(20, 10))

    # Entry Fields
    fields = ["NAME", "AGE", "PHONE NO.", "GMAIL ID", "PASSWORD", "CONFIRM PASSWORD"]
    entry_widgets = []

    for field in fields:
        # Label for each field
        label = ctk.CTkLabel(main_frame, text=field, font=("Arial", 14))
        label.pack(pady=(10, 0), anchor="w", padx=20)
        
        # Entry box for each field
        entry = ctk.CTkEntry(main_frame, placeholder_text=f"Enter {field.lower()}")
        entry.pack(pady=(5, 10), padx=20, fill="x")
        entry_widgets.append(entry)

    # Unpack entry widgets for readability
    name_entry, age_entry, phone_entry, email_entry, pass_entry, comp_pass_entry = entry_widgets

    # Submit Button
    submit_button = ctk.CTkButton(
        main_frame,
        text="Submit",
        fg_color="#6A0DAD",  # Purple color
        hover_color="#8A2BE2",  # Lighter purple on hover
        font=("Arial", 16),
        corner_radius=8,
        command=lambda: AddDetails(name_entry, age_entry, phone_entry, email_entry, pass_entry, comp_pass_entry, loginWindow)
    )
    submit_button.pack(pady=(10, 20))

    # Placeholder Logo Section
    logo_frame = ctk.CTkFrame(main_frame, fg_color="#DCDCEC", corner_radius=0)
    logo_frame.pack(pady=20, fill="x")

    logo_label1 = ctk.CTkLabel(logo_frame, text="TCA", font=("Times New Roman", 24, "bold"), text_color="#013C89")
    logo_label1.pack()

    logo_label2 = ctk.CTkLabel(logo_frame, text="The Creative Alchemists", font=("Arial", 14, "italic"), text_color="#009933")
    logo_label2.pack()


# Function to add user details to the database
def AddDetails(nameEntry, ageEntry, phoneEntry, emailEntry, passEntry, compassEntry, loginWindow):
    name = nameEntry.get()

    try:
        age = int(ageEntry.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid age.")
        return

    if not name or not ageEntry.get() or not phoneEntry.get() or not emailEntry.get():
        messagebox.showerror("Invalid Input", "All fields must be filled.")
        return
    
    if not phoneEntry.get().isdigit() or len(phoneEntry.get()) != 10:
        messagebox.showerror("Invalid Input", "Please enter a valid 10-digit phone number.")
        return

    if "@" not in emailEntry.get() or "." not in emailEntry.get():
        messagebox.showerror("Invalid Input", "Please enter a valid email address.")
        return

    if passEntry.get() != compassEntry.get():
        messagebox.showerror("Invalid Input", "Password does not match.")
        return

    # Insert details into the database
    try:
        cursor.execute("INSERT INTO user_data(name, age, phone, email, password) VALUES (?, ?, ?, ?, ?)", 
                       (name, age, phoneEntry.get(), emailEntry.get(), passEntry.get()))
        conn.commit()
        messagebox.showinfo("Success", f"Details for {name} have been submitted successfully.")
        loginWindow.destroy()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "User with this name already exists.")
        loginWindow.destroy()

# Create the main app page
def SignInPage():
    signInWindow = ctk.CTkToplevel()
    signInWindow.geometry("400x600")
    signInWindow.title("Sign In Page")

    # Add a back button
    #back_button = ctk.CTkButton(app, text="◀", width=30, height=30, font=("Arial", 16), fg_color="lightgray")
    #back_button.place(x=10, y=10)

    # Add the welcome text
    welcome_label = ctk.CTkLabel(signInWindow, text="Welcome!", font=("Arial", 28, "bold"), text_color="blue")
    welcome_label.pack(pady=(40, 0))

    sub_label = ctk.CTkLabel(signInWindow, text="Sign in to continue", font=("Arial", 16), text_color="gray")
    sub_label.pack()

    # Add the images (hat and clock)
    Books_image = Image.open(r"C:\Users\LENOVO\Downloads\WhatsApp Image 2024-11-26 at 11.40.42 AM.jpeg")
    Books_photo = CTkImage(Books_image, size=(180,180))

    #round borders
    #Books_image = round_image(r"C:\Users\hp\OneDrive\Pictures\Screenshots\Screenshot 2024-11-26 104640.png",100)

    Books_label = ctk.CTkLabel(signInWindow, image=Books_photo, text="")
    Books_label.place(x=110, y=100)


    # Add the login form
    form_frame = ctk.CTkFrame(signInWindow, width=320, height=200, corner_radius=15)
    form_frame.pack(pady=(180, 20))

    email_entry = ctk.CTkEntry(form_frame, placeholder_text="Username", width=280)
    email_entry.pack(pady=(20, 10))

    password_entry = ctk.CTkEntry(form_frame, placeholder_text="Password", show="*", width=280)
    password_entry.pack(pady=(10, 20))
    login_button = ctk.CTkButton(form_frame, text="LOGIN", width=280, height=40, font=("Arial", 14, "bold"),command=lambda:CheckDetails(email_entry,password_entry,signInWindow))
    login_button.pack(pady=(10, 10))

    # Add the "create account" link
    create_account_button = ctk.CTkButton(signInWindow, text="Create a new Account", font=("Arial", 12), text_color="blue",fg_color="lightgray",command=LoginPage)
    create_account_button.pack()


    # Run the application
    signInWindow.mainloop()


# Function to check user credentials
def CheckDetails(nameEntry, passEntry, signInWindow):
    name = nameEntry.get()
    password = passEntry.get()

    # Check if the user exists and the password matches
    cursor.execute("SELECT * FROM user_data WHERE name = ? AND password = ?", (name, password))
    user = cursor.fetchone()
    
    if user:
        messagebox.showinfo("Success", "Login successful.")
        signInWindow.destroy()
        if root.winfo_exists():
            root.withdraw()
        HomePage()  # Open HomePage upon successful login
    else:
        messagebox.showerror("Error", "Invalid name or password.")
        signInWindow.destroy()

def HomePage():
    homeWindow = tk.Toplevel()
    homeWindow.title("ElderCare Companion App")
    homeWindow.geometry("1000x550")
    homeWindow.configure(bg="#E1F7C6")  # Soft minty green background

    def load_image(path, size):
        image = Image.open(path)
        return ImageTk.PhotoImage(image)

    # Replace 'path_to_image' with the actual paths to your images
    photo1_path = r"C:\Users\LENOVO\Desktop\Longathon sem1\top banner.png"
    photo2_path = r"C:\Users\LENOVO\Desktop\Longathon sem1\bottom banner.png"
    photo3_path = r"C:\Users\LENOVO\Desktop\Longathon sem1\old lady photo.png"
    photo4_path = r"C:\Users\LENOVO\Downloads\together photo.png"

    # Load images
    photo1 = load_image(photo1_path, (200, 100))
    photo2 = load_image(photo2_path, (400, 50))
    photo3 = load_image(photo3_path, (200, 250))
    photo4 = load_image(photo4_path, (200, 100))

    # Position images using place()
    photo1_label = tk.Label(homeWindow, image=photo1, bg="#E1F7C6")
    photo1_label.place(x=0, y=0)

    photo4_label = tk.Label(homeWindow, image=photo4, bg="#E1F7C6")
    photo4_label.place(x=260, y=100)

    photo3_label = tk.Label(homeWindow, image=photo3, bg="#E1F7C6")
    photo3_label.place(x=554, y=60)

    photo2_label = tk.Label(homeWindow, image=photo2, bg="#E1F7C6")
    photo2_label.place(x=0, y=500)

    # Button font
    button_font = font.Font(family="Helvetica", size=12, weight="bold")


    scheButton = tk.Button(homeWindow, text="Scheduler", font=button_font,bg="#b6b59b",fg="black",width=20,height=2,command=Scheduler)
    scheButton.place(x=10,y=200)
    gameButton=tk.Button(homeWindow,text="Stress Buster Games",font=button_font,bg="#b6b59b",fg="black",width=20,height=2,command=gamePage)
    gameButton.place(x=10,y=380)
    DocButton = tk.Button(homeWindow, text="Doc Bot",font=button_font, bg="#b6b59b",fg="black",width=20,height=5,command=DocBot)
    DocButton.place(x=308,y=270)
    jonButton=tk.Button(homeWindow, text="Journal",font=button_font,bg="#b6b59b",fg="black",width=20,height=2,command=show_reports)
    jonButton.place(x=10,y=140)
    consulButton = tk.Button(homeWindow,text="Book Consultation",font=button_font,bg="#b6b59b",fg="black",width=20,height=2,command=Consultation)
    consulButton.place(x=10,y=320)
    callButton=tk.Button(homeWindow,text="Emergency Contact",font=button_font,bg="#b6b59b",fg="black",width=20,height=2,command=Call)
    callButton.place(x=10,y=260)

    homeWindow.mainloop()



def gamePage():
    gameWindow=tk.Toplevel()
    gameWindow.title="Stress Buster Games"
    gameWindow.geometry("500x400")

    def launch_game_flappy():

        if sys.platform == "win32":
            game_path = r"C:\Users\LENOVO\Desktop\MyGames\Unity\FlappyBird\FlappyBird.exe"
            
        else:
            messagebox.showerror("Error", "Unsupported platform.")
            return


        if not os.path.exists(game_path):
            messagebox.showerror("Error", f"Game executable not found at {game_path}.")
            return
        
        try:
            subprocess.Popen(game_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch the game: {e}")

    def launch_game_tic():
        gameWindow.geometry("600x400")
        current_player = "X"
        board = [["", "", ""], ["", "", ""], ["", "", ""]]

        # Function to check if a player has won
        def check_winner():
            for row in board:
                if row[0] == row[1] == row[2] != "":
                    return row[0]
            for col in range(3):
                if board[0][col] == board[1][col] == board[2][col] != "":
                    return board[0][col]
            if board[0][0] == board[1][1] == board[2][2] != "" or board[0][2] == board[1][1] == board[2][0] != "":
                return board[1][1]
            return None

        # Function to check if the board is full
        def is_board_full():
            return all(cell != "" for row in board for cell in row)

        # Function to handle button clicks
        def on_button_click(row, col):
            nonlocal current_player
            if board[row][col] == "":
                board[row][col] = current_player
                buttons[row][col].config(text=current_player)
                winner = check_winner()
                if winner:
                    messagebox.showinfo("Game Over", f"Player {winner} wins!")
                    reset_board()
                elif is_board_full():
                    messagebox.showinfo("Game Over", "It's a draw!")
                    reset_board()
                else:
                    current_player = "O" if current_player == "X" else "X"

        # Function to reset the board
        def reset_board():
            nonlocal current_player, board
            current_player = "X"
            board = [["", "", ""], ["", "", ""], ["", "", ""]]
            for row in range(3):
                for col in range(3):
                    buttons[row][col].config(text="")

        # Initialize a 3x3 grid of buttons
        buttons = [[None for _ in range(3)] for _ in range(3)]
        for row in range(3):
            for col in range(3):
                buttons[row][col] = tk.Button(gameWindow, text="", width=10, height=3, font=("Arial", 24),
                                              command=lambda r=row, c=col: on_button_click(r, c))
                buttons[row][col].grid(row=row, column=col)


# Call launch_game_tic() within gamePage() where gameWindow is already defined

    

    flappyButton=tk.Button(gameWindow,text="Flappy Bird",command=launch_game_flappy)
    flappyButton.place(x=150,y=200)
    ticButton=tk.Button(gameWindow,text="Tic-Tac-Toe",command=launch_game_tic)
    ticButton.place(x=250,y=200)
    hangButton=tk.Button(gameWindow,text="Hangman",command=Hangman)
    hangButton.place(x=350,y=200)
    gameWindow.mainloop()




def Scheduler():
    scheduleWindow = tk.Toplevel()
    scheduleWindow.title("Medicine Scheduler")

    # Entry fields
    name_label = tk.Label(scheduleWindow, text="Medicine Name:")
    name_label.grid(row=0, column=0)
    name_entry = tk.Entry(scheduleWindow)
    name_entry.grid(row=0, column=1)

    dose_label = tk.Label(scheduleWindow, text="Dose:")
    dose_label.grid(row=1, column=0)
    dose_entry = tk.Entry(scheduleWindow)
    dose_entry.grid(row=1, column=1)

    time_label = tk.Label(scheduleWindow, text="Time (HH:MM):")
    time_label.grid(row=2, column=0)
    time_entry = tk.Entry(scheduleWindow)
    time_entry.grid(row=2, column=1)

    # Listbox to display medicines
    medicine_display = tk.Listbox(scheduleWindow, width=50, selectmode=tk.SINGLE)
    medicine_display.grid(row=4, column=0, columnspan=2)

    medicine_file = "medicine_schedule.json"
    medicine_list = []

    def load_medicines():
        """Load medicines from a JSON file."""
        if os.path.exists(medicine_file):
            with open(medicine_file, "r") as file:
                data = json.load(file)
                for medicine in data:
                    medicine_list.append(tuple(medicine))
                    medicine_display.insert(tk.END, f"{medicine[0]} - {medicine[1]} - {medicine[2]}")

    def save_medicines():
        """Save medicines to a JSON file."""
        with open(medicine_file, "w") as file:
            json.dump(medicine_list, file)

    def add_medicine():
        """Adds a medicine to the list and displays it."""
        name = name_entry.get()
        dose = dose_entry.get()
        time_str = time_entry.get()

        if name and dose and time_str:
            try:
                # Validate time format
                time.strptime(time_str, "%H:%M")
                medicine_list.append((name, dose, time_str))
                medicine_display.insert(tk.END, f"{name} - {dose} - {time_str}")
                save_medicines()
                name_entry.delete(0, tk.END)
                dose_entry.delete(0, tk.END)
                time_entry.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Invalid Time", "Please enter time in HH:MM format.")
        else:
            messagebox.showwarning("Incomplete Data", "Please enter all fields.")

    def delete_medicine():
        """Deletes the selected medicine from the list."""
        selected_index = medicine_display.curselection()

        if selected_index:
            selected_index = selected_index[0]
            medicine_display.delete(selected_index)
            del medicine_list[selected_index]
            save_medicines()
        else:
            messagebox.showwarning("No Selection", "Please select a medicine to delete.")

    def check_reminders():
        """Checks if it's time for any medicine and shows a reminder."""
        current_time = time.strftime("%H:%M")
        for medicine in medicine_list:
            name, dose, med_time = medicine
            if med_time == current_time and (name, dose, med_time) not in reminded_today:
                messagebox.showinfo("Medicine Reminder", f"It's time to take your {name} ({dose})")
                reminded_today.add((name, dose, med_time))  # Mark reminder as shown

        # Reset reminders at midnight
        if current_time == "00:00":
            reminded_today.clear()

        # Schedule the next check in 60 seconds
        scheduleWindow.after(60000, check_reminders)

    # Add buttons
    add_button = tk.Button(scheduleWindow, text="Add Medicine", command=add_medicine)
    add_button.grid(row=3, column=0)

    delete_button = tk.Button(scheduleWindow, text="Delete Medicine", command=delete_medicine)
    delete_button.grid(row=3, column=1)

    # Initialize reminders tracking set (to prevent repeated notifications)
    reminded_today = set()

    # Load existing medicines from the file
    load_medicines()

    # Start the reminder checking function
    check_reminders()

    scheduleWindow.mainloop()


# File to store entries
FILE_NAME = "entries.txt"
entries=[]

import customtkinter as ctk
from tkinter import Listbox, messagebox


def show_reports():
    global entries

    def load_entries():
        """Load entries from the file."""
        try:
            with open(FILE_NAME, "r") as file:
                return [line.strip() for line in file.readlines()]
        except FileNotFoundError:
            return []

    def save_entries():
        """Save entries to the file."""
        with open(FILE_NAME, "w") as file:
            for entry in entries:
                file.write(entry + "\n")

    def refresh_listbox():
        """Refresh the listbox to show current entries."""
        listbox.delete(0, ctk.END)
        for entry in entries:
            listbox.insert(ctk.END, entry)

    def add_entry():
        """Add a new entry with a custom dialog."""

        def save_new_entry():
            new_entry = entry_field.get().strip()
            if new_entry:
                entries.append(new_entry)
                save_entries()
                refresh_listbox()
                add_window.destroy()
            else:
                messagebox.showerror("Error", "Entry cannot be empty.")

        add_window = ctk.CTkToplevel(root)
        add_window.title("Add Entry")
        add_window.geometry("400x200")

        ctk.CTkLabel(add_window, text="Enter a new entry:", font=("Arial", 16)).pack(pady=10)
        entry_field = ctk.CTkEntry(add_window, width=300, font=("Arial", 16))
        entry_field.pack(pady=10)

        save_button = ctk.CTkButton(add_window, text="Save", command=save_new_entry, font=("Arial", 14))
        save_button.pack(pady=10)

        entry_field.focus()

    def delete_entry():
        """Delete the selected entry."""
        try:
            selected_index = listbox.curselection()[0]
            selected_entry = listbox.get(selected_index)
            entries.remove(selected_entry)
            save_entries()
            refresh_listbox()
        except IndexError:
            messagebox.showerror("Error", "No entry selected to delete.")

    # Load entries from the file
    global entries
    entries = load_entries()

    # Create the main application window
    global root
    root = ctk.CTk()
    root.title("Entry Manager")
    root.geometry("600x500")

    ctk.CTkLabel(root, text="Entries List", font=("Arial", 20)).pack(pady=10)

    # Scrollable frame for the listbox
    listbox_frame = ctk.CTkScrollableFrame(root, width=400, height=300)
    listbox_frame.pack(pady=10)

    # Use a tk.Listbox within the scrollable frame
    listbox = Listbox(listbox_frame, height=15, width=40, font=("Arial", 14))
    listbox.pack(pady=5, padx=5)
    refresh_listbox()

    add_button = ctk.CTkButton(root, text="Add Entry", command=add_entry, font=("Arial", 14))
    add_button.pack(pady=5)

    delete_button = ctk.CTkButton(root, text="Delete Entry", command=delete_entry, font=("Arial", 14))
    delete_button.pack(pady=5)

    root.mainloop()



def Consultation():
    consulWindow=tk.Toplevel()
    consulWindow.title("Doctors in your area")
    consulWindow.geometry("400x400")
    def search_doctors():
        area = area_entry.get().strip()
        disease = disease_entry.get().strip()
        
        if not area and not disease:
            messagebox.showwarning("Input Error", "Please enter at least an area or a disease.")
            return
        
        query = "doctors"
        if disease:
            query += f" for {disease}"
        if area:
            query += f" in {area}"
        
        search_url = f"https://www.google.com/search?q={query}"
        webbrowser.open(search_url)

    tk.Label(consulWindow, text="Enter Area:").pack(pady=5)
    area_entry = tk.Entry(consulWindow, width=40)
    area_entry.pack(pady=5)

    # Disease input
    tk.Label(consulWindow, text="Enter Disease:").pack(pady=5)
    disease_entry = tk.Entry(consulWindow, width=40)
    disease_entry.pack(pady=5)

    # Search button
    search_button = tk.Button(consulWindow, text="Search Doctors", command=search_doctors)
    search_button.pack(pady=20)

    # Run the application
    consulWindow.mainloop()


import tkinter as tk
from tkinter import messagebox
from twilio.rest import Client  # Make sure this import is included

def initiate_call(account_sid, auth_token, to_number, from_number, message):
    """
    Initiates a call using Twilio and plays a message using TwiML.
    """
    try:
        # Create a Twilio client
        client = Client(account_sid, auth_token)
        
        # Make the call
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            twiml=f"""
            <Response>
                <Say voice="alice">{message}</Say>
            </Response>
            """
        )
        return call.sid
    except Exception as e:
        raise RuntimeError(f"Failed to initiate call: {e}")

def make_call():
    """
    Initiates the call when the button is pressed.
    """
    # Define the emergency number and message
    emergency_number = '+918172895307'  # Replace with the actual emergency number
    person_name = "asmita"  # Replace with the actual person's name
    from_number = '+12029522859'  # Replace with your Twilio number
    message = f"Hello, this is a call from ElderCare for {person_name}. This is an SOS call. Please respond as soon as possible."

    # Define Twilio credentials (replace with your own)
    account_sid = 'AC05517661fbb4f7eccb7ba7e03e2e161d'
    auth_token = 'dd004575b18b13f22921e70890434f31'

    try:
        # Initiate the call
        call_sid = initiate_call(account_sid, auth_token, emergency_number, from_number, message)
        messagebox.showinfo("Call Initiated", f"Call initiated successfully.\nCall SID: {call_sid}")
    except RuntimeError as e:
        messagebox.showerror("Call Failed", str(e))

def Call():
    # Tkinter GUI
    root = tk.Tk()
    root.title("ElderCare SOS Call")

    # Create a big "Make Call" button
    call_button = tk.Button(
        root, text="Make Call", font=("Arial", 24), bg="green", fg="white", command=make_call,
        height=4, width=20  # Adjust the size of the button
    )
    call_button.pack(pady=50)

    # Center the Tkinter window
    root.eval('tk::PlaceWindow . center')

    # Start Tkinter main loop
    root.mainloop()


def Hangman():
    hangman.main()


root = tk.Tk()
root.title("Eldercare Login Window")
root.geometry("1500x550")
root.configure(bg="#ecece8")

def load_image(path):
    image=Image.open(path)
    return ImageTk.PhotoImage(image)

#old lady
photo1_PATH=r"C:\Users\LENOVO\Downloads\WhatsApp Image 2024-11-23 at 1.11.33 AM.jpeg"
#Eldercare banner
photo2_PATH=r"C:\Users\LENOVO\Downloads\WhatsApp Image 2024-11-23 at 1.11.32 AM.jpeg"
#Side quote
photo3_PATH=r"C:\Users\LENOVO\Downloads\WhatsApp Image 2024-11-26 at 1.55.20 PM.jpeg"
#Sign in bg effect
photo4_PATH=r"C:\Users\LENOVO\Downloads\WhatsApp Image 2024-11-23 at 1.11.04 AM.jpeg"

#Loading Image
Photo1=load_image(photo1_PATH)
Photo2=load_image(photo2_PATH)
Photo3=load_image(photo3_PATH)
Photo4=load_image(photo4_PATH)

#Image Fitting
Photo1_label=tk.Label(root, image=Photo1,bg='#ecece8')
Photo1_label.place(x=0,y=0)

Photo2_label=tk.Label(root,image=Photo2,bg="#ecece8")
Photo2_label.place(x=360,y=0)

Photo3_label=tk.Label(root,image=Photo3,bg="#ecece8")
Photo3_label.place(x=1090,y=0)

Photo4_label=tk.Label(root,image=Photo4,bg="#ecece8")
Photo4_label.place(x=500,y=400)

Photo5_label=tk.Label(root, image=Photo4,bg="#ecece8")
Photo5_label.place(x=800,y=400)

# Button font
button_font = font.Font(family="Times New Roman", size=30, weight="bold")

#Button
def create_button(text, x, y,func, color="#ecece8", fg_color="black", width=6, height=0):
    button = tk.Button(root, text=text, font=button_font, bg=color, fg=fg_color, width=width, height=height,command=func)
    button.place(x=x, y=y)
    return button

create_button("Sign Up",528,420,LoginPage)
create_button("Sign In",828,420,SignInPage)

root.mainloop()

# Close the database connection when done
conn.close()
connD.close()

