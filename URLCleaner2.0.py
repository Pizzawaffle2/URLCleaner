import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import *
import re
from collections import defaultdict
from urllib.parse import urlparse, urlunparse
import logging
import os

url_history = []

# Set up logging
log_file_path = 'app.log'
if not os.path.exists(log_file_path):
    open(log_file_path, 'a').close()
logging.basicConfig(filename=log_file_path, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the main application window
root = ttk.Window(themename='darkly')
root.title("URL Cleaner")

# Main frame for widget organization
main_frame = ttk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Adding Menus after main_frame to ensure correct order
menu_bar = Menu(root)
root.config(menu=menu_bar)

#"Find" Menu option implementation
def open_find_dialog():
    find_window = Toplevel(root)
    find_window.title("Find")

    # Label and Entry for Find
    Label(find_window, text="Find:").pack(side="left")
    find_entry = Entry(find_window)
    find_entry.pack(side="left", fill="x", expand=True)
    find_entry.focus_set()

    def find_next():
        search_term = find_entry.get()
        start = '1.0'
        while True:
            start = url_entry.search(search_term, start, stopindex="end")
            if not start:
                break
            end = f"{start}+{len(search_term)}c"
            url_entry.tag_add("search", start, end)
            start = end
        url_entry.tag_config("search", background="yellow")

    Button(find_window, text="Find Next", command=find_next).pack(side="right")

#"Replace" Menu Option Implementation
def open_replace_dialog():
    replace_window = Toplevel(root)
    replace_window.title("Replace")

    # Find and Replace Fields
    Label(replace_window, text="Find:").pack(side="left")
    find_entry = Entry(replace_window)
    find_entry.pack(side="left", fill="x", expand=True)

    Label(replace_window, text="Replace:").pack(side="left")
    replace_entry = Entry(replace_window)
    replace_entry.pack(side="left", fill="x", expand=True)
    find_entry.focus_set()

    def replace_all():
        search_term = find_entry.get()
        replace_term = replace_entry.get()
        content = url_entry.get("1.0", "end-1c")
        new_content = content.replace(search_term, replace_term)
        url_entry.delete("1.0", "end")
        url_entry.insert("1.0", new_content)

    Button(replace_window, text="Replace All", command=replace_all).pack(side="right")

# Define url_entry here to ensure it exists before being referenced
url_entry_frame = ttk.Frame(main_frame)
url_entry_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)
url_entry = Text(url_entry_frame, height=10, wrap="none", undo=True)  # Enable undo
url_scroll = Scrollbar(url_entry_frame, orient="vertical", command=url_entry.yview)
url_entry.config(yscrollcommand=url_scroll.set)
url_scroll.pack(side="right", fill="y")
url_entry.pack(side="left", fill="both", expand=True)

# Menus (File, Edit, History, Themes, Help)
file_menu = Menu(menu_bar, tearoff=0)
edit_menu = Menu(menu_bar, tearoff=0)  # Edit menu added
history_menu = Menu(menu_bar, tearoff=0)
theme_menu = Menu(menu_bar, tearoff=0)
help_menu = Menu(menu_bar, tearoff=0)

# Adding cascades for menus
menu_bar.add_cascade(label="File", menu=file_menu)
menu_bar.add_cascade(label="Edit", menu=edit_menu)  # Add Edit menu to menu bar
menu_bar.add_cascade(label="History", menu=history_menu)
menu_bar.add_cascade(label="Themes", menu=theme_menu)
menu_bar.add_cascade(label="Help", menu=help_menu)

# Populate the theme menu with available themes
for theme in root.style.theme_names():
    theme_menu.add_command(label=theme, command=lambda theme=theme: root.style.theme_use(theme))

# File Menu Commands
file_menu.add_command(label="Save to Notepad", command=lambda: save_to_notepad())
file_menu.add_command(label="Copy to Clipboard", command=lambda: copy_to_clipboard())
file_menu.add_command(label="Import URLs", command=lambda: import_urls())

# Edit Menu Commands implementation
edit_menu.add_command(label="Undo", command=lambda: url_entry.edit_undo())
edit_menu.add_command(label="Redo", command=lambda: url_entry.edit_redo())
edit_menu.add_separator()
edit_menu.add_command(label="Cut", command=lambda: url_entry.event_generate("<<Cut>>"))
edit_menu.add_command(label="Copy", command=lambda: url_entry.event_generate("<<Copy>>"))
edit_menu.add_command(label="Paste", command=lambda: url_entry.event_generate("<<Paste>>"))
edit_menu.add_separator()
edit_menu.add_command(label="Find", command=open_find_dialog)
edit_menu.add_command(label="Replace", command=open_replace_dialog)

# Ensure url_entry widget has undo enabled and is focusable
url_entry.config(undo=True)
url_entry.focus_set()

# History Menu Command
history_menu.add_command(label="View History", command=lambda: open_history_window())

# Help Menu Commands
help_menu.add_command(label="User Guide", command=lambda: open_user_guide())
help_menu.add_command(label="About", command=lambda: show_about_dialog())

# Function to create and show the context menu
def make_context_menu(widget):
    context_menu = Menu(widget, tearoff=0)
    context_menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    context_menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    context_menu.add_command(label="Select All", command=lambda: widget.tag_add("sel", "1.0", "end"))
    context_menu.add_command(label="Clear", command=lambda: widget.delete('1.0', 'end'))

    def show_context_menu(event):
        if widget.winfo_containing(event.x_root, event.y_root) == widget:
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

    widget.bind("<Button-3>", show_context_menu)

# URL validation function
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# URL host extraction function
def extract_url_host(url):
    if is_valid_url(url):
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"
    return None

# Function to categorize URLs
def categorize_urls(urls):
    categories = defaultdict(list)
    for url in urls:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        categories[domain].append(url)
    return categories

# Clean URLs function
def clean_urls():
    global categorized_urls, url_history
    input_text = url_entry.get("1.0", "end-1c").strip()
    urls = re.split(r'[\n;]\s*', input_text)
    cleaned_urls = set()
    host_urls = set()

    for url in urls:
        if not url:
            continue
        if url.startswith("*."):
            url = url[2:]
        if not re.match(r'^https?://', url):
            url = 'https://' + url

        try:
            if is_valid_url(url):
                parsed_url = urlparse(url)
                normalized_path = re.sub(r'/+', '/', parsed_url.path)
                normalized_url = urlunparse(parsed_url._replace(scheme=parsed_url.scheme.lower(), path=normalized_path))
                cleaned_urls.add(normalized_url)
                host = extract_url_host(normalized_url)
                if host:
                    host_urls.add(host)
        except Exception as e:
            logging.error(f"Error processing URL: {url}\nError: {str(e)}")

    if cleaned_urls:  # Ensure there's something to add
        url_history.append(list(cleaned_urls))  # Convert set to list and append to history
    update_text_widgets(cleaned_urls, host_urls)

# Function to update the Text widgets and categorize URLs
def update_text_widgets(cleaned_urls, host_urls):
    cleaned_urls_text.delete("1.0", "end")
    cleaned_urls_text.insert("end", "Full URL:\n" + "\n".join(sorted(cleaned_urls)))
    host_urls_text.delete("1.0", "end")
    host_urls_text.insert("end", "URL Host:\n" + "\n".join(sorted(host_urls)))

# Function to save cleaned URLs to a notepad file
def save_to_notepad():
    text = cleaned_urls_text.get("1.0", "end-1c")
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Documents", "*.txt")])
    if file_path:
        with open(file_path, "w") as f:
            f.write(text)
        messagebox.showinfo("Success", "Cleaned URLs saved to '{}'".format(file_path))

# Function to copy cleaned URLs to the clipboard
def copy_to_clipboard():
    text = cleaned_urls_text.get("1.0", "end-1c")
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    messagebox.showinfo("Success", "Cleaned URLs copied to clipboard!")

# Function to import URLs from a file
def import_urls():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "r") as file:
            urls = file.read()
        url_entry.delete("1.0", "end")
        url_entry.insert("1.0", urls)
        messagebox.showinfo("Success", "URLs imported successfully!")

# Define and place widgets in the main_frame
url_label = ttk.Label(main_frame, text="Enter URLs (each on a new line):")
url_label.grid(row=0, column=0, padx=(0, 10), sticky="W")

url_entry_frame = ttk.Frame(main_frame)
url_entry_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)
url_entry = Text(url_entry_frame, height=10, wrap="none")
url_scroll = Scrollbar(url_entry_frame, orient="vertical", command=url_entry.yview)
url_entry.config(yscrollcommand=url_scroll.set)
url_scroll.pack(side="right", fill="y")
url_entry.pack(side="left", fill="both", expand=True)
make_context_menu(url_entry)

# Protocol Radio Buttons
protocol_var = IntVar(value=0)
port_80_radio = ttk.Radiobutton(main_frame, text="Port 80 (http)", variable=protocol_var, value=1)
port_443_radio = ttk.Radiobutton(main_frame, text="Port 443 (https)", variable=protocol_var, value=0)
port_80_radio.grid(row=2, column=0, sticky="W")
port_443_radio.grid(row=2, column=1, sticky="W")

# Centered Clean URLs Button
clean_button_frame = ttk.Frame(main_frame)
clean_button_frame.grid(row=3, column=0, columnspan=2, pady=(5, 0))
clean_button = ttk.Button(clean_button_frame, text="Clean URLs", command=clean_urls)
clean_button.pack()

# Display areas for URLs and Hosts with Labels
cleaned_urls_label = ttk.Label(main_frame, text="Full URL:")
cleaned_urls_label.grid(row=4, column=0, sticky="W")
cleaned_urls_frame = ttk.Frame(main_frame)
cleaned_urls_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=5)
cleaned_urls_text = Text(cleaned_urls_frame, height=10)
cleaned_scroll = Scrollbar(cleaned_urls_frame, orient="vertical", command=cleaned_urls_text.yview)
cleaned_urls_text.config(yscrollcommand=cleaned_scroll.set)
cleaned_scroll.pack(side="right", fill="y")
cleaned_urls_text.pack(side="left", fill="both", expand=True)

host_urls_label = ttk.Label(main_frame, text="URL Host:")
host_urls_label.grid(row=6, column=0, sticky="W")
host_urls_frame = ttk.Frame(main_frame)
host_urls_frame.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=5)
host_urls_text = Text(host_urls_frame, height=10)
host_scroll = Scrollbar(host_urls_frame, orient="vertical", command=host_urls_text.yview)
host_urls_text.config(yscrollcommand=host_scroll.set)
host_scroll.pack(side="right", fill="y")
host_urls_text.pack(side="left", fill="both", expand=True)

# User Guide and About Dialog Functions
def open_user_guide():
    guide_window = Toplevel(root)
    guide_window.title("User Guide")
    guide_text = Text(guide_window, wrap="word", height=15, width=50)
    guide_text.pack(padx=10, pady=10, fill="both", expand=True)
    guide_info = """Welcome to the URL Cleaner Application User Guide
    
- Enter URLs in the text box at the top.
- Use the 'Clean URLs' button to process them.
- The cleaned URLs will appear in the 'Full URL' area, with their subdirectory still attatched.
- The extracted hosts will be listed under 'URL Host' (As in, subdirectories removed from URL).
- Use the 'File' menu for additional options like saving and importing URLs.
- Usage of "Find" or "Replace" with no field will crash the app.
- Themes are changeable, However they will not presist amongst future sessions. This is a future consideration.
"""
    guide_text.insert("1.0", guide_info)
    guide_text.config(state="disabled")

def show_about_dialog():
    messagebox.showinfo("About URL Cleaner", 
    "URL Cleaner Application\nVersion: 1.0\nAuthor: Brendan Makidon\nLicense: MIT License\nThis application cleans and processes URLs, providing both cleaned URLs and extracted host names.")

# Open History Window
def open_history_window():
    history_window = Toplevel(root)
    history_window.title("URL Cleaning History")
    history_listbox = Listbox(history_window, width=50, height=10)
    history_listbox.pack(padx=10, pady=10, fill="both", expand=True)
    for i, entry in enumerate(url_history, start=1):
        history_listbox.insert('end', f"History {i}: {len(entry)} URLs")
    
    def on_history_select(event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            selected_urls = url_history[index]
            url_entry.delete('1.0', 'end')
            for url in selected_urls:
                url_entry.insert('end', url + '\n')
    history_listbox.bind('<<ListboxSelect>>', on_history_select)

# Configure the main frame grid
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_rowconfigure(5, weight=1)

root.mainloop()

#Created by BrendanMakidon