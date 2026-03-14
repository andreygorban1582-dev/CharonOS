import tkinter as tk
from tkinter import scrolledtext
import threading
from assistant.speech import listen, speak
from assistant.brain import get_response
from doom.launcher import launch_doom


class RickAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rick Assistant")
        self.root.geometry("600x500")
        self.root.configure(bg='#1e1e1e')

        # Chat display
        self.chat_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, width=70, height=20,
            bg='#2d2d2d', fg='#00ff00', font=('Courier', 10)
        )
        self.chat_area.pack(padx=10, pady=10)
        self.chat_area.config(state=tk.DISABLED)

        # Input frame
        input_frame = tk.Frame(root, bg='#1e1e1e')
        input_frame.pack(pady=5)

        self.input_entry = tk.Entry(
            input_frame, width=50, bg='#3d3d3d', fg='white', insertbackground='white'
        )
        self.input_entry.pack(side=tk.LEFT, padx=5)
        self.input_entry.bind("<Return>", self.send_text)

        send_btn = tk.Button(input_frame, text="Send", command=self.send_text, bg='#0078d7', fg='white')
        send_btn.pack(side=tk.LEFT)

        # Voice button
        voice_btn = tk.Button(root, text="🎤 Voice", command=self.start_voice, bg='#0078d7', fg='white')
        voice_btn.pack(pady=5)

        # Doom button
        doom_btn = tk.Button(root, text="🔥 Play DOOM", command=self.play_doom, bg='#b22222', fg='white')
        doom_btn.pack(pady=5)

        self.conversation_history = []
        self.display_message("Rick", "*burp* What do you want, Morty?")

    def display_message(self, sender, message):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"{sender}: {message}\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def send_text(self, event=None):
        user_input = self.input_entry.get()
        if not user_input:
            return
        self.display_message("You", user_input)
        self.input_entry.delete(0, tk.END)

        # Run AI in background to avoid freezing GUI
        threading.Thread(target=self.process_ai, args=(user_input,), daemon=True).start()

    def process_ai(self, user_input):
        reply, self.conversation_history = get_response(user_input, self.conversation_history)
        self.root.after(0, self.display_message, "Rick", reply)
        self.root.after(0, lambda: speak(reply))

    def start_voice(self):
        threading.Thread(target=self.voice_thread, daemon=True).start()

    def voice_thread(self):
        user_input = listen()
        if user_input:
            self.root.after(0, self.display_message, "You (voice)", user_input)
            reply, self.conversation_history = get_response(user_input, self.conversation_history)
            self.root.after(0, self.display_message, "Rick", reply)
            self.root.after(0, lambda: speak(reply))

    def play_doom(self):
        threading.Thread(target=launch_doom, daemon=True).start()


def run_gui():
    root = tk.Tk()
    app = RickAssistantGUI(root)
    root.mainloop()
