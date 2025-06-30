import csv
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from logic.converter import Converter
import platform
import re
import json
import io
import urllib.parse
import random
import datetime
import uuid
import ast, json

converter = Converter()

# 这些第三方库延迟导入
yaml = None
xmltodict = None
jsonpath_ng = None

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

# GUI 主构建函数
def build_gui(root):
    root.title("多格式数据解析与转换工具")
    root.geometry("900x700")
    root.minsize(900, 900)

    # 输入区域
    tk.Label(root, text="输入区域").pack(anchor='w', padx=10, pady=(10, 0))
    input_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=15, font=get_monospace_font(11), name="input_text")
    input_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # 操作区（下拉菜单）
    action_frame = tk.Frame(root, bg="lightgray")
    action_frame.pack(fill=tk.X, padx=11, pady=11)
    tk.Label(action_frame, text="选择操作：").pack(side=tk.LEFT)
    selected_action = tk.StringVar()
    combo = ttk.Combobox(action_frame, textvariable=selected_action, state="readonly",
                         values=[
                             "打开文件",
                         "XML 转 JSON",
                         "YAML 转 JSON",
                         "CSV 转 JSON",
                         "URL 参数转 JSON",
                         "Excel 转 JSON",
                         "格式化输出",
                         "压缩输出",
                         "复制结果",
                         "保存结果",
                         "生成模板"
                         ])
    combo.pack(side=tk.LEFT, padx=5)
    combo.set("请选择")

    # 输出区域
    tk.Label(root, text="输出区域").pack(anchor='w', padx=10)
    output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=15, font=get_monospace_font(11))
    output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # 查找/替换/JSONPath/导航/暗黑模式控件
    control_frame = tk.Frame(root)
    control_frame.pack(fill=tk.X, padx=10, pady=5)

    tk.Label(control_frame, text="查找").grid(row=0, column=0, sticky="w")
    find_entry = tk.Entry(control_frame, width=15)
    find_entry.grid(row=0, column=1)

    tk.Label(control_frame, text="替换").grid(row=0, column=2, sticky="w")
    replace_entry = tk.Entry(control_frame, width=15)
    replace_entry.grid(row=0, column=3)

    find_btn = tk.Button(control_frame, text="查找", command=lambda: search_text(output_text, find_entry, nav_label))
    find_btn.grid(row=0, column=4, padx=2)
    replace_btn = tk.Button(control_frame, text="替换", command=lambda: replace_text(output_text, find_entry, replace_entry))
    replace_btn.grid(row=0, column=5, padx=2)
    replace_all_btn = tk.Button(control_frame, text="全部替换", command=lambda: replace_all_text(output_text, find_entry, replace_entry))
    replace_all_btn.grid(row=0, column=6, padx=2)

    tk.Label(control_frame, text="JSONPath").grid(row=1, column=0, sticky="w", pady=(5, 0))
    jsonpath_entry = tk.Entry(control_frame, width=40)
    jsonpath_entry.grid(row=1, column=1, columnspan=3, pady=(5, 0))
    jsonpath_btn = tk.Button(control_frame, text="提取", command=lambda: run_jsonpath(output_text, jsonpath_entry))
    jsonpath_btn.grid(row=1, column=4, padx=2, pady=(5, 0))

    nav_label = tk.Label(control_frame, text="")
    nav_label.grid(row=1, column=5, columnspan=2, sticky="w", padx=5)

    dark_mode_var = tk.BooleanVar(value=False)
    def toggle_dark():
        toggle_dark_mode(dark_mode_var.get(), root, [input_text, output_text, find_entry, replace_entry, jsonpath_entry])
        dark_mode_var.set(not dark_mode_var.get())
    dark_btn = tk.Button(control_frame, text="切换暗黑模式", command=toggle_dark)
    dark_btn.grid(row=1, column=7, padx=5, pady=(5, 0))
    
    def clear_all():
        input_text.delete("1.0", tk.END)
        output_text.delete("1.0", tk.END)
        nav_label.config(text="")

    combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    clear_btn = tk.Button(action_frame, text="🧹 一键清除", command=clear_all, bg="#002c69", fg="white")
    clear_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=2)

    

    # 防抖计时器变量
    debounce_id = None

    # 自动解析输入并更新输出，带防抖
    def try_parse_and_update():
        nonlocal debounce_id
        debounce_id = None
        raw = input_text.get("1.0", tk.END).strip()
        if not raw:
            output_text.delete("1.0", tk.END)
            nav_label.config(text="")
            return
        try:
            data = auto_parse(raw)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, formatted)
            highlight_json(output_text)
            nav_label.config(text="")
        except Exception as e:
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, f"解析失败: {e}")
            nav_label.config(text="")

    def on_input_change(event):
        nonlocal debounce_id
        input_text.edit_modified(False)
        if debounce_id:
            root.after_cancel(debounce_id)
        debounce_id = root.after(600, try_parse_and_update)

    input_text.bind('<<Modified>>', on_input_change)

    # 操作按钮实现
    def open_file():
        path = filedialog.askopenfilename(filetypes=[
            ("支持的文件", "*.json *.yaml *.yml *.xml *.csv"),
            ("所有文件", "*.*")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                input_text.delete("1.0", tk.END)
                input_text.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("打开失败", str(e))

    def format_output():
        raw = output_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("提示", "输出为空，无法格式化")
            return
        try:
            data = auto_parse(raw)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, formatted)
            highlight_json(output_text)
        except Exception as e:
            messagebox.showerror("格式化失败", str(e))

    def minify_output():
        raw = output_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("提示", "输出为空，无法压缩")
            return
        try:
            data = auto_parse(raw)
            minified = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, minified)
            highlight_json(output_text)
        except Exception as e:
            messagebox.showerror("压缩失败", str(e))

    def copy_output():
        text = output_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("提示", "输出为空，无法复制")
            return
        root.clipboard_clear()
        root.clipboard_append(text)
        messagebox.showinfo("复制成功", "内容已复制到剪贴板")

    def save_output():
        content = output_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("提示", "输出为空，无法保存")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")])
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("保存成功", f"文件已保存：{path}")
            except Exception as e:
                messagebox.showerror("保存失败", str(e))

    def generate_template(schema):
        def gen_value(v):
            if isinstance(v, str):
                type_map = {
                    "string": lambda: random.choice(["张三", "李四", "测试数据", "示例"]),
                    "name": lambda: random.choice(["李雷", "韩梅梅", "小红", "王大锤"]),
                    "number": lambda: random.randint(1, 100),
                    "int": lambda: random.randint(1, 100),
                    "float": lambda: round(random.uniform(0, 100), 2),
                    "boolean": lambda: random.choice([True, False]),
                    "null": lambda: None,
                    "date": lambda: str(datetime.date.today()),
                    "time": lambda: str(datetime.datetime.now().time())[:8],
                    "email": lambda: f"user{random.randint(1,100)}@example.com",
                    "uuid": lambda: str(uuid.uuid4()),
                    "url": lambda: f"https://example.com/page/{random.randint(1, 100)}",
                    "avatar": lambda: f"https://i.pravatar.cc/150?img={random.randint(1,70)}",
                    "phone": lambda: f"1{random.choice(['3','5','7','8','9'])}{random.randint(100000000,999999999)}",
                    "address": lambda: random.choice([
                        "北京市朝阳区三里屯街道",
                        "上海市浦东新区张江路",
                        "广州市天河区体育西路",
                        "深圳市南山区科技园"
                    ])
                }
                return type_map.get(v.lower(), lambda: v)()
            elif isinstance(v, list) and len(v) == 1:
                return [gen_value(v[0])]
            elif isinstance(v, dict):
                return {k: gen_value(vv) for k, vv in v.items()}
            return v
        return gen_value(schema)

    def generate_from_schema():
        raw = input_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("提示", "输入为空，无法生成模板")
            return
        try:
            schema = json.loads(raw)
            result = generate_template(schema)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, json.dumps(result, indent=2, ensure_ascii=False))
            highlight_json(output_text)
        except Exception as e:
            messagebox.showerror("模板生成失败", str(e))
            
    def xml_to_json_action():
        raw = input_text.get("1.0", tk.END).strip()
        try:
            data = converter.xml_to_json(raw)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
            highlight_json(output_text)
        except Exception as e:
            messagebox.showerror("XML 解析失败", str(e))

    def yaml_to_json_action():
        raw = input_text.get("1.0", tk.END).strip()
        try:
            data = converter.yaml_to_json(raw)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
            highlight_json(output_text)
        except Exception as e:
            messagebox.showerror("YAML 解析失败", str(e))

    def csv_to_json_action():
        raw = input_text.get("1.0", tk.END).strip()
        try:
            data = converter.csv_to_json(raw)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
            highlight_json(output_text)
        except Exception as e:
            messagebox.showerror("CSV 解析失败", str(e))

    def url_to_json_action():
        raw = input_text.get("1.0", tk.END).strip()
        try:
            data = converter.url_to_json(raw)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
            highlight_json(output_text)
        except Exception as e:
            messagebox.showerror("URL 解析失败", str(e))

    def excel_to_json_action():
        path = filedialog.askopenfilename(filetypes=[("Excel 文件", "*.xls *.xlsx")])
        if not path:
            return
        try:
            data = converter.excel_to_json(path)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
            highlight_json(output_text)
        except Exception as e:
             messagebox.showerror("Excel 解析失败", str(e))

    # 绑定下拉框动作
    func_map = {
        "打开文件": open_file,
    "XML 转 JSON": xml_to_json_action,
    "YAML 转 JSON": yaml_to_json_action,
    "CSV 转 JSON": csv_to_json_action,
    "URL 参数转 JSON": url_to_json_action,
    "Excel 转 JSON": excel_to_json_action,
    "格式化输出": format_output,
    "压缩输出": minify_output,
    "复制结果": copy_output,
    "保存结果": save_output,
    "生成模板": generate_from_schema
    }

    def on_action_selected(event):
        action_name = selected_action.get()
        func = func_map.get(action_name)
        if func:
            func()
        combo.set("")  
        combo.after(10, lambda: combo.set(action_name))

    combo.bind("<<ComboboxSelected>>", on_action_selected)

    return input_text, output_text, find_entry, replace_entry, jsonpath_entry, nav_label
