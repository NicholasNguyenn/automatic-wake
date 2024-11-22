import tkinter as tk
import agent as agent


# Class to render GUI when main driver class is running. Allows for a visual representation of the robot's state and allows for user input.
class GUI:
    def __init__(self, toggle_recording, get_robot_response):
        self.master = tk.Tk()
        self.master.title("Audio Recorder")
        self.master.geometry("1200x800")

        self.exit_clicked = False

        self.master.option_add("*font", "lucida 18")

        self.toggle_recording = toggle_recording
        self.get_response = get_robot_response

        # Create GUI elements
        header_frame = tk.Frame(self.master)
        tk.Label(header_frame, text="Dobby").pack(side=tk.LEFT, padx=5, pady=5)
        self.state_label = tk.Label(header_frame, text="CONVERSING")
        self.state_label.pack(side=tk.RIGHT, padx=5, pady=5)
        textbox_frame = tk.Frame(self.master)
        tk.Label(textbox_frame, text="Chat:").pack(side=tk.LEFT, padx=5, pady=5)
        self.chat_line = tk.StringVar(self.master, value="")
        self.chat_entry = tk.Entry(textbox_frame, textvariable=self.chat_line)
        self.chat_entry.pack(expand=True, fill="x", padx=5, pady=5)
        self.chat_entry.bind("<Return>", self.submit_chat)
        button_frame = tk.Frame(self.master)
        self.record_button = tk.Button(
            button_frame, text="Record", command=self.toggle_recording
        )
        self.record_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.hey_dobby_mode = tk.BooleanVar(self.master, True)
        quit_button = tk.Button(button_frame, text="Quit", command=self.quit)
        quit_button.pack(side=tk.RIGHT, padx=5, pady=5)
        c1 = tk.Checkbutton(
            button_frame,
            text="Hey Dobby",
            variable=self.hey_dobby_mode,
            onvalue=True,
            offvalue=False,
        )
        c1.pack(side=tk.RIGHT)
        button_frame.pack(side=tk.BOTTOM, expand=True, fill="x")
        textbox_frame.pack(side=tk.BOTTOM, expand=True, fill="x")
        self.console = tk.Text(self.master, wrap=tk.WORD, state="disabled")
        header_frame.pack(side=tk.TOP, expand=True, fill="x")
        self.console.pack(side=tk.BOTTOM, expand=True, fill="both")
        self.console.tag_config("system", foreground="orange")

        self.record_button.config(state=tk.DISABLED)
        self.chat_entry.config(state=tk.DISABLED)
        self.master.after(2000, self.initial_setup)

        self.current_response_phrase = ""
        self.approaching_person = False

    def initial_setup(self):
        self.record_button.config(state=tk.NORMAL)
        self.chat_entry.config(state=tk.NORMAL)

    def submit_chat(self, event):
        self.toggle_recording(False)
        chat = self.chat_line.get()
        if len(chat) > 0:
            self.chat_line.set("")
            self.get_response(chat)

    def log_console(self, text, system=False, end="\n"):
        self.console.config(state=tk.NORMAL)
        if system:
            self.console.insert(tk.END, text + end, "system")
        else:
            self.console.insert(tk.END, text + end)
        self.console.config(state=tk.DISABLED)
        self.console.see(tk.END)
        if agent.get_state() != "CONVERSING":
            self.state_label.config(text=agent.get_state(), fg="blue")
        else:
            self.state_label.config(text=agent.get_state(), fg="black")
        self.master.update_idletasks()

    def display_recording(self, recording):
        if recording:
            self.record_button.config(text="Stop", fg="red")
        else:
            self.record_button.config(text="Record", fg="black")
        self.master.update_idletasks()

    def enable_recording(self, enabled):
        self.record_button.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def enable_input(self, enabled):
        self.chat_entry.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def quit(self):
        self.exit_clicked = True
        self.master.destroy()

    def is_exit_clicked(self):
        return self.exit_clicked

    def update(self):
        self.master.update()
        self.master.update_idletasks()
