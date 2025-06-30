import tkinter as tk
from tkinter import  messagebox
from logic.converter import Converter
import platform
import re
import json
import urllib.parse
import ast, json
import demjson3 

converter = Converter()

def lazy_import_yaml():
    global yaml
    if yaml is None:
        import yaml

def lazy_import_xmltodict():
    global xmltodict
    if xmltodict is None:
        import xmltodict

def lazy_import_jsonpath():
    global jsonpath_ng
    if jsonpath_ng is None:
        from jsonpath_ng import parse as jsonpath_parse
        jsonpath_ng = jsonpath_parse

def auto_parse(raw_text):
    raw_text = raw_text.strip()
    
    # 如果输入包含多个对象，尝试分别解析
    if raw_text.count('}') > 1:
        try:
            # 将输入按 } 分割，然后重新组合每个对象
            parts = [part + '}' for part in raw_text.split('}') if part.strip()]
            results = []
            for part in parts:
                try:
                    if not part.startswith('{'):
                        part = '{' + part
                    results.append(demjson3.decode(part))
                except Exception:
                    continue
            if results:
                return results[0] if len(results) == 1 else results
        except Exception:
            pass
    
    # 首先尝试使用 demjson3 解析 JavaScript 格式
    try:
        return demjson3.decode(raw_text)
    except Exception:
        pass
    
    # 然后尝试标准 JSON 解析
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(raw_text)
        except Exception:
            pass

    try:
        lazy_import_yaml()
        return yaml.safe_load(raw_text)
    except Exception:
        pass

    try:
        lazy_import_xmltodict()
        return xmltodict.parse(raw_text)
    except Exception:
        pass

    try:
        return xmltodict.parse(raw_text)
    except Exception:
        pass

    if ',' in raw_text and '\n' in raw_text:
        try:
            return converter.csv_to_json(raw_text)
        except Exception:
            pass

    if '=' in raw_text:
        try:
            return converter.url_to_json(raw_text)
        except Exception:
            pass
    try:
        parsed = dict(urllib.parse.parse_qsl(raw_text))
        if parsed and '=' in raw_text:
            return parsed
    except Exception:
        pass

    raise ValueError("无法识别输入格式")

# 获取等宽字体
def get_monospace_font(size=10):
    system = platform.system()
    if system == "Windows":
        return ("Consolas", size)
    elif system == "Darwin":
        return ("Menlo", size)
    else:
        return ("Monospace", size)

# JSON 语法高亮
def highlight_json(text_widget):
    text = text_widget.get("1.0", "end-1c")
    for tag in ("string", "number", "keyword"):
        text_widget.tag_remove(tag, "1.0", "end")

    for match in re.finditer(r'\".*?\"', text):
        start = f"1.0 + {match.start()} chars"
        end = f"1.0 + {match.end()} chars"
        text_widget.tag_add("string", start, end)

    for match in re.finditer(r'\b\d+(\.\d+)?\b', text):
        start = f"1.0 + {match.start()} chars"
        end = f"1.0 + {match.end()} chars"
        text_widget.tag_add("number", start, end)

    for kw in ["true", "false", "null"]:
        start = "1.0"
        while True:
            pos = text_widget.search(kw, start, tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(kw)}c"
            text_widget.tag_add("keyword", pos, end)
            start = end

    text_widget.tag_config("string", foreground="#d14")
    text_widget.tag_config("number", foreground="#099")
    text_widget.tag_config("keyword", foreground="#44f")

# 查找所有关键字并高亮，支持导航
def search_text(output_text, find_entry, nav_label):
    keyword = find_entry.get()
    output_text.tag_remove("found", "1.0", tk.END)
    if not keyword:
        nav_label.config(text="")
        return
    idx = "1.0"
    matches = []
    while True:
        idx = output_text.search(keyword, idx, nocase=True, stopindex=tk.END)
        if not idx:
            break
        lastidx = f"{idx}+{len(keyword)}c"
        output_text.tag_add("found", idx, lastidx)
        matches.append(idx)
        idx = lastidx
    output_text.tag_config("found", background="yellow")
    if matches:
        nav_label.config(text=f"找到 {len(matches)} 处")
    else:
        nav_label.config(text="未找到")

# 查找并跳转到下一个匹配
def navigate_next(output_text, find_entry, nav_label):
    keyword = find_entry.get()
    if not keyword:
        return
    current_pos = output_text.index(tk.INSERT)
    next_pos = output_text.search(keyword, f"{current_pos}+1c", nocase=True, stopindex=tk.END)
    if not next_pos:
        # 回到开头
        next_pos = output_text.search(keyword, "1.0", nocase=True, stopindex=tk.END)
    if next_pos:
        output_text.mark_set(tk.INSERT, next_pos)
        output_text.see(next_pos)
        nav_label.config(text=f"跳转至 {next_pos}")

# 替换第一个匹配
def replace_text(output_text, find_entry, replace_entry):
    keyword = find_entry.get()
    replacement = replace_entry.get()
    idx = output_text.search(keyword, "1.0", tk.END)
    if idx:
        end = f"{idx}+{len(keyword)}c"
        output_text.delete(idx, end)
        output_text.insert(idx, replacement)

# 替换所有匹配
def replace_all_text(output_text, find_entry, replace_entry):
    keyword = find_entry.get()
    replacement = replace_entry.get()
    content = output_text.get("1.0", tk.END)
    new_content = content.replace(keyword, replacement)
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, new_content)

# 暗黑模式切换
def toggle_dark_mode(is_dark_mode, root, widgets):
    if is_dark_mode:
        root.config(bg="#1e1e1e")
        for w in widgets:
            w.config(bg="#2d2d2d", fg="#d4d4d4", insertbackground="white")
    else:
        root.config(bg="SystemButtonFace")
        for w in widgets:
            w.config(bg="white", fg="black", insertbackground="black")

# JSONPath 提取显示到输出框，不弹窗
def run_jsonpath(output_text, jsonpath_entry):
    expr = jsonpath_entry.get().strip()
    raw = output_text.get("1.0", tk.END).strip()
    if not expr:
        messagebox.showwarning("提示", "请输入 JSONPath 表达式")
        return
    try:
        data = json.loads(raw)
    except Exception as e:
        messagebox.showerror("错误", f"输出不是合法 JSON：\n{e}")
        return
    try:
        lazy_import_jsonpath()
        jsonpath_expr = jsonpath_ng(expr)
        result = [match.value for match in jsonpath_expr.find(data)]
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, json.dumps(result, indent=2, ensure_ascii=False))
        highlight_json(output_text)
    except Exception as e:
        messagebox.showerror("JSONPath 错误", str(e))
