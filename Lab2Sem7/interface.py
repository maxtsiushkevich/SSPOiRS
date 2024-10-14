import tkinter as tk
from tkinter import ttk


def create_label(parent, text, relx, rely, font=('Arial', 14)):
    label = tk.Label(parent, text=text, font=font)
    label.place(relx=relx, rely=rely)
    return label


def create_input_entry(parent, width, relx, rely, bind_function=None, action='<Return>'):
    input_entry = tk.Entry(parent, width=width)
    input_entry.place(relx=relx, rely=rely)

    if bind_function is not None:
        input_entry.bind(action, lambda event: bind_function())

    return input_entry


def create_text_widget(parent, width, height, relx, rely):
    text_widget = tk.Text(parent, width=width, height=height, state='disabled')
    text_widget.place(relx=relx, rely=rely)
    return text_widget


def update_textbox(text_widget, text):
    text_widget.config(state='normal')
    text_widget.insert(tk.END, text + '\n')
    text_widget.config(state='disabled')
    text_widget.see(tk.END)


def clear_text_widget(text_widget):
    text_widget.config(state='normal')
    text_widget.delete('1.0', tk.END)
    text_widget.config(state='disabled')
