import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3 as sql

# Global variable for the current list
current_list = None

# Function to create a new list
def create_list():
    global current_list
    new_list_name = list_name_field.get()
    if new_list_name == "":
        messagebox.showinfo('Error', 'List Name Cannot Be Empty.')
        return

    # Add the new list to the database
    the_cursor.execute('insert into lists (name) values (?)', (new_list_name,))
    the_connection.commit()

    # Clear the entry field
    list_name_field.delete(0, 'end')

    # Refresh the list of lists
    refresh_lists()

    # Automatically switch to the new list
    current_list = new_list_name
    retrieve_tasks()
    list_update()

# Function to retrieve lists from the database
def refresh_lists():
    list_box.delete(0, 'end')
    for row in the_cursor.execute('select name from lists'):
        list_box.insert('end', row[0])

# Function to select a list
def select_list(event):
    global current_list
    current_list = list_box.get(list_box.curselection())
    retrieve_tasks()
    list_update()

# Function to delete a list
def delete_list():
    global current_list
    if current_list is None:
        messagebox.showinfo('Error', 'No List Selected.')
        return

    # Confirm deletion
    message_box = messagebox.askyesno('Delete List', f'Are you sure you want to delete "{current_list}"?')
    if message_box:
        the_cursor.execute('delete from lists where name = ?', (current_list,))
        the_cursor.execute('delete from tasks where list_name = ?', (current_list,))
        the_connection.commit()
        current_list = None  # Reset current list
        refresh_lists()  # Refresh the displayed lists
        clear_tasks()  # Clear tasks from the UI

# Function to retrieve tasks for the current list
def retrieve_tasks():
    global tasks
    tasks.clear()
    for row in the_cursor.execute('select title, completed from tasks where list_name = ?', (current_list,)):
        tasks.append((row[0], row[1]))

# Function to add tasks to the current list
def add_task():
    task_string = task_field.get()
    if len(task_string) == 0:
        messagebox.showinfo('Error', 'Field is Empty.')
    else:
        tasks.append((task_string, 0))
        the_cursor.execute('insert into tasks (title, completed, list_name) values (?, ?, ?)', (task_string, 0, current_list))
        the_connection.commit()
        list_update()
        task_field.delete(0, 'end')

def list_update():
    clear_tasks()
    for i, (task, completed) in enumerate(tasks):
        task_var = tk.BooleanVar(value=completed)
        checkbox = tk.Checkbutton(
            task_listbox_frame,
            text=task,
            variable=task_var,
            onvalue=1,
            offvalue=0,
            command=lambda t=task, var=task_var: toggle_task(t, var),
            font=("Consolas", 12),  # Set font size to 20
            bg=task_listbox_frame.cget("bg")  # Keep background color consistent
        )
        checkbox.pack(anchor='w', padx=10, pady=5)  # Padding for better spacing
        checkbox.task_var = task_var
        checkbox.task_name = task

def toggle_task(task, var):
    status = var.get()
    for i, (t, _) in enumerate(tasks):
        if t == task:
            tasks[i] = (task, status)
            the_cursor.execute('update tasks set completed = ? where title = ? and list_name = ?', (status, task, current_list))
    list_update()

def delete_task():
    checkbuttons = task_listbox_frame.winfo_children()
    for checkbox in checkbuttons:
        if checkbox.task_var.get():
            selected_task = checkbox.task_name
            tasks[:] = [(task, completed) for task, completed in tasks if task != selected_task]
            the_cursor.execute('delete from tasks where title = ? and list_name = ?', (selected_task, current_list))
            the_connection.commit()
            list_update()
            return
    messagebox.showinfo('Error', 'No Task Selected. Cannot Delete.')

def delete_all_tasks():
    if current_list is None:
        messagebox.showinfo('Error', 'No List Selected.')
        return
    message_box = messagebox.askyesno('Delete All', 'Are you sure?')
    if message_box:
        tasks.clear()
        the_cursor.execute('delete from tasks where list_name = ?', (current_list,))
        the_connection.commit()
        list_update()

def clear_tasks():
    for widget in task_listbox_frame.winfo_children():
        widget.destroy()

def close():
    guiWindow.destroy()

def setup_database():
    the_cursor.execute('create table if not exists lists (name text)')
    the_cursor.execute('create table if not exists tasks (title text, completed integer, list_name text)')

if __name__ == "__main__":
    # Creating the main window
    guiWindow = tk.Tk()
    guiWindow.title("CHECKMATE")
    guiWindow.geometry("850x600+650+200")  # Increased window size to provide more space for functions_frame
    guiWindow.resizable(0, 0)
    guiWindow.configure(bg="#FAEBD7")

    # Connect to the database
    the_connection = sql.connect('task_lists.db')
    the_cursor = the_connection.cursor()
    setup_database()

    # Creating frames
    functions_frame = tk.Frame(guiWindow, bg="#FAEBD7", width=650)  # Functions frame width for 3/4 of window
    task_listbox_frame = tk.Frame(guiWindow, relief="sunken", bd=2, width=200)  # Task list box frame width for 1/4 of window

    # Apply chessboard-like background pattern for the entire frame
    chessboard_bg = ["#FFFACD", "#DEB887"]  # LightYellow and BurlyWood colors for alternating pattern
    task_listbox_frame.configure(bg=chessboard_bg[0])  # Starting color for the frame background

    lists_frame = tk.Frame(guiWindow, bg="#FAEBD7", height=100)  # Top section for lists

    functions_frame.pack(side="left", expand=False, fill="y", padx=10, pady=10)  # Vertical fill to expand the frame
    task_listbox_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)
    lists_frame.pack(side="top", expand=False, fill="x", padx=10, pady=10)

    # Entry for new list name
    list_name_field = ttk.Entry(lists_frame, font=("Consolas", 12), width=20)
    list_name_field.pack(pady=10)

    create_list_button = ttk.Button(lists_frame, text="Create List", command=create_list)
    create_list_button.pack(pady=5)

    delete_list_button = ttk.Button(lists_frame, text="Delete Selected List", command=delete_list)
    delete_list_button.pack(pady=5)

    # Listbox for lists
    list_box = tk.Listbox(lists_frame, width=30, height=5)
    list_box.pack(pady=10)
    list_box.bind('<<ListboxSelect>>', select_list)

    # Task entry and buttons
    task_field = ttk.Entry(functions_frame, font=("Consolas", 12), width=20)
    task_field.pack(pady=10)

    add_task_button = ttk.Button(functions_frame, text="Add Task", command=add_task)
    add_task_button.pack(pady=5)

    delete_task_button = ttk.Button(functions_frame, text="Delete Task", command=delete_task)
    delete_task_button.pack(pady=5)

    delete_all_button = ttk.Button(functions_frame, text="Delete All Tasks", command=delete_all_tasks)
    delete_all_button.pack(pady=5)

    exit_button = ttk.Button(functions_frame, text="Exit", command=close)
    exit_button.pack(pady=5)

    # Task list display
    task_listbox_frame.pack(side="right", expand=True, fill="both", padx=10)

    # Initialize the tasks list
    tasks = []

    # Load existing lists
    refresh_lists()

    guiWindow.mainloop()

    the_connection.commit()
    the_cursor.close()
