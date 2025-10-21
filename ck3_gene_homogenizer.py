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
        for event in ("<KeyRelease>", "<MouseWheel>", "<Button-1>", "<ButtonRelease-1>", "<Configure>"): #
            self.text_widget.bind(event, self.redraw)
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
        self.geometry("1600x600")
        self.configure(bg="#2e2e2e")

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TLabel", foreground="#dddddd", background="#2e2e2e")
        style.configure("TButton", foreground="#ffffff", background="#555555")

        main_container = tk.Frame(self, bg="#2e2e2e")
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # LEFT SIDE
        left_side = tk.Frame(main_container, bg="#2e2e2e")
        left_side.pack(side="left", fill="both", expand=True, padx=(0, 5))

        input_header = tk.Frame(left_side, bg="#2e2e2e")
        input_header.pack(fill="x", pady=(0, 5))
        ttk.Label(input_header, text="Input DNA String (Drag & Drop or Paste)").pack(side="left")
        ttk.Button(input_header, text="Clear", command=self.clear_input, width=8).pack(side="right")

        self.input_frame = tk.Frame(left_side, bg="#3a3a3a")
        self.input_frame.pack(fill="both", expand=True)
        self.input_text = tk.Text(self.input_frame, wrap="none", bg="#1e1e1e", fg="#eeeeee", insertbackground='white', font=("Consolas", 11))
        self.input_text.pack(side="right", fill="both", expand=True)
        for ev in ("<KeyRelease>", "<<Paste>>", "<ButtonRelease-2>"):
            self.input_text.bind(ev, self.on_input_change_delayed)

        self.linenumbers_in = LineNumbers(self.input_frame, self.input_text, width=40, bg="#3a3a3a")
        self.linenumbers_in.pack(side="left", fill="y")

        scroll_y_in = ttk.Scrollbar(self.input_frame, orient="vertical", command=self.on_scroll_in)
        scroll_y_in.pack(side="right", fill="y")
        self.input_text.config(yscrollcommand=scroll_y_in.set)

        # RIGHT SIDE
        right_side = tk.Frame(main_container, bg="#2e2e2e")
        right_side.pack(side="right", fill="both", expand=True, padx=(5, 0))

        output_header = tk.Frame(right_side, bg="#2e2e2e")
        output_header.pack(fill="x", pady=(0, 5))
        ttk.Label(output_header, text="Processed DNA Output").pack(side="left")
        ttk.Button(output_header, text="Copy", command=self.copy_output, width=8).pack(side="right")

        self.output_frame = tk.Frame(right_side, bg="#3a3a3a")
        self.output_frame.pack(fill="both", expand=True)
        self.output_text = tk.Text(self.output_frame, wrap="none", bg="#111722", fg="#aaffff", insertbackground='white', font=("Consolas", 11), state="disabled")
        self.output_text.pack(side="right", fill="both", expand=True)

        self.linenumbers_out = LineNumbers(self.output_frame, self.output_text, width=40, bg="#3a3a3a")
        self.linenumbers_out.pack(side="left", fill="y")

        scroll_y_out = ttk.Scrollbar(self.output_frame, orient="vertical", command=self.on_scroll_out)
        scroll_y_out.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=scroll_y_out.set)

        if tkinterdnd2:
            self.input_text.drop_target_register(tkinterdnd2.DND_FILES)
            self.input_text.dnd_bind('<<Drop>>', self.drop_file)

        self.status_label = ttk.Label(self, text="Idle - Paste or drag DNA file to process", background="#2e2e2e", foreground="#888888")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

    def clear_input(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.status_label.config(text="Idle - Paste or drag DNA file to process")
        self.linenumbers_in.redraw()
        self.linenumbers_out.redraw()

    def copy_output(self):
        data = self.output_text.get("1.0", tk.END).strip()
        if data:
            self.clipboard_clear()
            self.clipboard_append(data)
            self.status_label.config(text="Copied to clipboard!")
            self.after(2000, lambda: self.status_label.config(text="Done - Output ready to copy"))
        else:
            messagebox.showinfo("Info", "No output to copy.")

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
        data = event.data.strip()
        # strip braces from drag-drop
        if data.startswith('{') and data.endswith('}'):
            data = data[1:-1]
        path = data
        if os.path.isfile(path) and path.lower().endswith('.txt'):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert(tk.END, content)
                self.on_input_change()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file:\n{e}")
        else:
            messagebox.showwarning("Warning", "Please drop a .txt file only.")
        return "break"

    def on_input_change_delayed(self, event=None):
        self.after(100, self.on_input_change)

    def on_input_change(self, event=None):
        text = self.input_text.get("1.0", tk.END)
        if not text.strip():
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
        processed_lines = []
        pattern = re.compile(
            r'^(\s*[\w_]+\s*=\s*\{\s*)'
            r'(\"[^\"]+\"|\d+)\s+'
            r'(\d+)\s+'
            r'(\"[^\"]+\"|\d+)\s+'
            r'(\d+)\s*'
            r'(\})',
            re.MULTILINE
        )
        for line in input_text.splitlines():
            match = pattern.match(line)
            if match:
                new_line = "{}{} {} {} {} {}".format(
                    match.group(1),
                    match.group(2),
                    match.group(3),
                    match.group(2),
                    match.group(3),
                    match.group(6)
                )
                processed_lines.append(new_line)
            else:
                processed_lines.append(line)
        return "\n".join(processed_lines)

if __name__ == "__main__":
    root = GeneProcessorGUI()
    root.mainloop()
