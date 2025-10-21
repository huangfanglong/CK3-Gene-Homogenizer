# CK3-Gene-Homogenizer

A Python application to **"homogenize" Crusader Kings 3 character DNA data**.

---

## Features

- Copy & paste CK3 DNA or drag-and-drop `.txt` files containing DNA data  
- Instantly outputs the processed DNA to the right pane  
- One-click **Clear** for both input/output fields  
- One-click **Copy** of processed DNA to clipboard  
- Build as a standalone executable with **PyInstaller** (no Python install required)

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/huangfanglong/CK3-Gene-Homogenizer.git
   cd CK3-Gene-Homogenizer
   ```

2. **Install dependencies**
   ```bash
   pip install tkinterdnd2
   ```

3. **Run the GUI**
   ```bash
   python ck3_gene_homogenizer.py
   ```
   Or simply run the pre-built .exe executable.

---

## Usage

### Input
- Paste **raw CK3 DNA text** into the left pane  
- Or **drag and drop** a `.txt` file containing CK3 DNA data

### Processing
- The right pane updates **instantly**  
- Each line of DNA is transformed from:
  ```
  gene_name={ val1 num1 val2 num2 }
  ```
  to
  ```
  gene_name={ val1 num1 val1 num1 }
  ```

### Output
- Click **Copy** to copy the processed DNA to the clipboard  
- Click **Clear** to reset both input and output panes  

---

## Build Executable (Optional)
To create a standalone `.exe` file:
```bash
pyinstaller --onefile --noconsole ck3_gene_homogenizer.py
```

---

## 📜 License
This project is open-source and available under the [MIT License](LICENSE).
