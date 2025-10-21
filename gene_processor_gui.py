import tkinter as tk
from tkinter import ttk, messagebox
import re
import os

try:
    import tkinterdnd2
except ImportError:
    tkinterdnd2 = None
    print("tkinterdnd2 not found, drag-and-drop support disabled")


class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget
        self.text_widget.bind("<KeyRelease>", self.redraw)
        self.text_widget.bind("<MouseWheel>", self.redraw)
        self.text_widget.bind("<Button-1>", self.redraw)
        self.text_widget.bind("<ButtonRelease-1>", self.redraw)
        self.text_widget.bind("<Configure>", self.redraw)
        self.redraw()

    def redraw(self, event=None):
        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2, y, anchor="nw", text=linenum, fill="#666666", font=("Consolas", 10))
            i = self.text_widget.index(f"{i}+1line")


class GeneProcessorGUI(tkinterdnd2.Tk if tkinterdnd2 else tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("CK3 Gene Homogenizer")
        self.geometry("1000x600")
        self.configure(bg="#2e2e2e")

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TLabel", foreground="#dddddd", background="#2e2e2e")
        style.configure("TButton", foreground="#ffffff", background="#555555")

        # Create main container for both sides
        main_container = tk.Frame(self, bg="#2e2e2e")
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # LEFT SIDE - Input
        left_side = tk.Frame(main_container, bg="#2e2e2e")
        left_side.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Header frame for label and clear button
        input_header = tk.Frame(left_side, bg="#2e2e2e")
        input_header.pack(fill="x", pady=(0, 5))

        label_input = ttk.Label(input_header, text="Input DNA String (Drag & Drop or Paste)")
        label_input.pack(side="left")

        clear_button = ttk.Button(input_header, text="Clear", command=self.clear_input, width=8)
        clear_button.pack(side="right")

        # Input text frame
        self.input_frame = tk.Frame(left_side, bg="#3a3a3a")
        self.input_frame.pack(fill="both", expand=True)

        self.input_text = tk.Text(self.input_frame, wrap="none", bg="#1e1e1e", fg="#eeeeee", 
                                  insertbackground='white', font=("Consolas", 11))
        self.input_text.pack(side="right", fill="both", expand=True)

        # Bind multiple events for input changes
        self.input_text.bind("<KeyRelease>", self.on_input_change)
        self.input_text.bind("<<Paste>>", self.on_input_change_delayed)
        self.input_text.bind("<ButtonRelease-2>", self.on_input_change_delayed)

        self.linenumbers_in = LineNumbers(self.input_frame, self.input_text, width=40, bg="#3a3a3a")
        self.linenumbers_in.pack(side="left", fill="y")

        scroll_y_in = ttk.Scrollbar(self.input_frame, orient="vertical", command=self.on_scroll_in)
        scroll_y_in.pack(side="right", fill="y")
        self.input_text.config(yscrollcommand=scroll_y_in.set)

        # RIGHT SIDE - Output
        right_side = tk.Frame(main_container, bg="#2e2e2e")
        right_side.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Output header
        output_header = tk.Frame(right_side, bg="#2e2e2e")
        output_header.pack(fill="x", pady=(0, 5))

        label_output = ttk.Label(output_header, text="Processed DNA Output")
        label_output.pack(side="left")

        copy_button = ttk.Button(output_header, text="Copy", command=self.copy_output, width=8)
        copy_button.pack(side="right")

        # Output text frame
        self.output_frame = tk.Frame(right_side, bg="#3a3a3a")
        self.output_frame.pack(fill="both", expand=True)

        self.output_text = tk.Text(self.output_frame, wrap="none", bg="#111722", fg="#aaffff", 
                                   insertbackground='white', font=("Consolas", 11), state="normal")
        self.output_text.pack(side="right", fill="both", expand=True)
        self.output_text.config(state=tk.DISABLED)

        self.linenumbers_out = LineNumbers(self.output_frame, self.output_text, width=40, bg="#3a3a3a")
        self.linenumbers_out.pack(side="left", fill="y")

        scroll_y_out = ttk.Scrollbar(self.output_frame, orient="vertical", command=self.on_scroll_out)
        scroll_y_out.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=scroll_y_out.set)

        # Drag and drop support
        if tkinterdnd2:
            self.input_text.drop_target_register(tkinterdnd2.DND_FILES)
            self.input_text.dnd_bind('<<Drop>>', self.drop_file)

        # Status bar at bottom
        self.status_label = ttk.Label(self, text="Idle - Paste or drag DNA file to process", 
                                     background="#2e2e2e", foreground="#888888")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

    def clear_input(self):
        """Clear both input and output boxes."""
        self.input_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.status_label.config(text="Idle - Paste or drag DNA file to process")
        self.linenumbers_in.redraw()
        self.linenumbers_out.redraw()

    def copy_output(self):
        """Copy the processed DNA output to clipboard."""
        output_content = self.output_text.get("1.0", tk.END).strip()
        if output_content:
            self.clipboard_clear()
            self.clipboard_append(output_content)
            self.status_label.config(text="Copied to clipboard!")
            # Reset status after 2 seconds
            self.after(2000, lambda: self.status_label.config(text="Done - Output ready to copy"))
        else:
            messagebox.showinfo("Info", "No output to copy. Please process some DNA first.")

    def on_scroll_in(self, *args):
        self.input_text.yview(*args)
        self.output_text.yview_moveto(self.input_text.yview()[0])
        self.linenumbers_in.redraw()
        self.linenumbers_out.redraw()

    def on_scroll_out(self, *args):
        self.output_text.yview(*args)
        self.input_text.yview_moveto(self.output_text.yview()[0])
        self.linenumbers_in.redraw()
        self.linenumbers_out.redraw()

    def drop_file(self, event):
        paths = self.split_drop_files(event.data)
        if paths:
            path = paths[0]
            if os.path.isfile(path) and path.lower().endswith('.txt'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = f.read()
                    self.input_text.delete("1.0", tk.END)
                    self.input_text.insert(tk.END, data)
                    self.on_input_change()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to read file:\n{e}")
            else:
                messagebox.showwarning("Warning", "Please drop a .txt file only.")
        return "break"

    @staticmethod
    def split_drop_files(data):
        if data.startswith('{') and data.endswith('}'):
            data = data[1:-1]
        return data.split()

    def on_input_change_delayed(self, event=None):
        self.after(100, self.on_input_change)

    def on_input_change(self, event=None):
        text = self.input_text.get("1.0", tk.END)

        if len(text.strip()) == 0:
            self.status_label.config(text="Idle - Paste or drag DNA file to process")
            return

        self.status_label.config(text="Processing...")
        self.update_idletasks()

        processed = self.process_gene_data(text)

        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, processed)
        self.output_text.config(state=tk.DISABLED)

        self.status_label.config(text="Done - Output ready to copy")
        self.linenumbers_out.redraw()

    @staticmethod
    def process_gene_data(input_text):
        """Process gene data by replacing last 2 values with first 2 values."""
        processed_lines = []

        line_pattern = re.compile(
            r'^(\s*[\w_]+\s*=\s*\{\s*)'
            r'(\"[^\"]+\"|\d+)\s+'
            r'(\d+)\s+'
            r'(\"[^\"]+\"|\d+)\s+'
            r'(\d+)\s*'
            r'(\})'
        )

        for line in input_text.splitlines():
            match = line_pattern.match(line)
            if match:
                new_line = "{}{} {} {} {} {}".format(
                    match.group(1), match.group(2), match.group(3),
                    match.group(2), match.group(3), match.group(6)
                )
                processed_lines.append(new_line)
            else:
                processed_lines.append(line)

        return "\n".join(processed_lines)


if __name__ == "__main__":
    root = GeneProcessorGUI()
    root.mainloop()
