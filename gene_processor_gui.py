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
        style.configure("TButton", foreground="#333333")

        label_input = ttk.Label(self, text="Input DNA String (Drag & Drop or Paste)")
        label_input.pack(anchor='nw', padx=10, pady=5)

        self.input_frame = tk.Frame(self, bg="#3a3a3a")
        self.input_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        self.input_text = tk.Text(self.input_frame, wrap="none", bg="#1e1e1e", fg="#eeeeee", 
                                  insertbackground='white', font=("Consolas", 11))
        self.input_text.pack(side="right", fill="both", expand=True)

        # Bind multiple events for input changes
        self.input_text.bind("<KeyRelease>", self.on_input_change)
        self.input_text.bind("<<Paste>>", self.on_input_change_delayed)
        self.input_text.bind("<ButtonRelease-2>", self.on_input_change_delayed)  # Middle mouse paste

        self.linenumbers_in = LineNumbers(self.input_frame, self.input_text, width=40, bg="#3a3a3a")
        self.linenumbers_in.pack(side="left", fill="y")

        label_output = ttk.Label(self, text="Processed DNA Output")
        label_output.pack(anchor='nw', padx=10, pady=5)

        self.output_frame = tk.Frame(self, bg="#3a3a3a")
        self.output_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

        self.output_text = tk.Text(self.output_frame, wrap="none", bg="#111722", fg="#aaffff", 
                                   insertbackground='white', font=("Consolas", 11), state="normal")
        self.output_text.pack(side="right", fill="both", expand=True)
        self.output_text.config(state=tk.DISABLED)

        self.linenumbers_out = LineNumbers(self.output_frame, self.output_text, width=40, bg="#3a3a3a")
        self.linenumbers_out.pack(side="left", fill="y")

        scroll_y_in = ttk.Scrollbar(self.input_frame, orient="vertical", command=self.on_scroll_in)
        scroll_y_in.pack(side="right", fill="y")
        self.input_text.config(yscrollcommand=scroll_y_in.set)

        scroll_y_out = ttk.Scrollbar(self.output_frame, orient="vertical", command=self.on_scroll_out)
        scroll_y_out.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=scroll_y_out.set)

        if tkinterdnd2:
            self.input_text.drop_target_register(tkinterdnd2.DND_FILES)
            self.input_text.dnd_bind('<<Drop>>', self.drop_file)

        self.status_label = ttk.Label(self, text="Idle - Paste or drag DNA file to process", 
                                     background="#2e2e2e", foreground="#888888")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

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
                    # Trigger processing after file load
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
        # For paste events, delay slightly to ensure text is inserted
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

        # Pattern matches: gene_name={ val1 num1 val2 num2 }
        line_pattern = re.compile(
            r'^(\s*[\w_]+\s*=\s*\{\s*)'      # gene name and opening brace
            r'(\"[^\"]+\"|\d+)\s+'            # val1 (quoted string or number)
            r'(\d+)\s+'                           # num1
            r'(\"[^\"]+\"|\d+)\s+'            # val2 (to be replaced)
            r'(\d+)\s*'                           # num2 (to be replaced)
            r'(\})'                                # closing brace
        )

        for line in input_text.splitlines():
            match = line_pattern.match(line)
            if match:
                # Replace val2/num2 with val1/num1
                new_line = "{}{} {} {} {} {}".format(
                    match.group(1),  # prefix with gene name and {
                    match.group(2),  # val1
                    match.group(3),  # num1
                    match.group(2),  # val1 again (replacing val2)
                    match.group(3),  # num1 again (replacing num2)
                    match.group(6)   # closing }
                )
                processed_lines.append(new_line)
            else:
                # Keep line as-is if no match
                processed_lines.append(line)

        return "\n".join(processed_lines)


if __name__ == "__main__":
    root = GeneProcessorGUI()
    root.mainloop()
