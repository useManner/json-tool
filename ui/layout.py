import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from logic.converter import Converter
from logic.comm import (
    toggle_dark_mode,
    auto_parse,
    get_monospace_font,
    highlight_json,
    search_text,
    replace_text,
    replace_all_text,
    run_jsonpath
)
import json
import random
import datetime
import uuid

converter = Converter()

# 这些第三方库延迟导入
yaml = None
xmltodict = None
jsonpath_ng = None


# GUI 主构建函数
def build_gui(root):
    root.title("多格式数据解析与转换工具")
    root.geometry("1200x800")  # 增加窗口大小以适应树形视图
    root.minsize(1200, 800)

    # 创建左右分栏
    left_frame = ttk.Frame(root)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    right_frame = ttk.Frame(root)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # 输入区域（左侧）
    tk.Label(left_frame, text="输入区域").pack(anchor='w', padx=10, pady=(10, 0))
    input_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, height=15, font=get_monospace_font(11), name="input_text")
    input_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # 操作区（左侧）
    action_frame = ttk.Frame(left_frame)
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

    # 输出区域（左侧）
    tk.Label(left_frame, text="输出区域").pack(anchor='w', padx=10)
    output_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, height=15, font=get_monospace_font(11))
    output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # JSON 树形视图（右侧）
    tk.Label(right_frame, text="JSON 树形视图").pack(anchor='w', padx=10, pady=(10, 0))
    from logic.treeview import JSONTreeView
    tree_view = JSONTreeView(right_frame)
    tree_view.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # 查找/替换/JSONPath/导航/暗黑模式控件
    control_frame = tk.Frame(left_frame)
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
        tree_view.delete(*tree_view.get_children())
        find_entry.delete(0, tk.END)
        replace_entry.delete(0, tk.END)
        jsonpath_entry.delete(0, tk.END)
        nav_label.config(text="")

    # 添加清除按钮
    clear_button = ttk.Button(action_frame, text="清除", command=clear_all)
    clear_button.pack(side=tk.LEFT, padx=5)

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

    def generate_from_schema():
        """根据输入的 JSON Schema 生成示例数据"""
        raw = input_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("提示", "请先输入 JSON Schema")
            return
        try:
            schema = json.loads(raw)
            result = converter.generate_template(schema)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, json.dumps(result, indent=2, ensure_ascii=False))
            highlight_json(output_text)
            # 更新树形视图
            tree_view.load(result)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Schema 格式错误", str(e))
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

    # 更新解析函数
    def parse_and_show():
        raw = input_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("提示", "请先输入内容")
            return
        try:
            # 清除旧的树形视图数据
            tree_view.delete(*tree_view.get_children())
            
            data = auto_parse(raw)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, formatted)
            highlight_json(output_text)
            
            # 重新加载树形视图
            tree_view.load(data)
        except Exception as e:
            messagebox.showerror("解析失败", str(e))

    # 更新操作处理函数
    def on_action_selected(event):
        action = selected_action.get()
        if action == "请选择":
            return
            
        raw = input_text.get("1.0", tk.END).strip()
        if not raw and action != "打开文件":
            messagebox.showwarning("提示", "请先输入内容")
            return

        try:
            result = None
            if action == "打开文件":
                open_file()
                return
            elif action == "XML 转 JSON":
                result = converter.xml_to_json(raw)
            elif action == "YAML 转 JSON":
                result = converter.yaml_to_json(raw)
            elif action == "CSV 转 JSON":
                result = converter.csv_to_json(raw)
            elif action == "URL 参数转 JSON":
                result = converter.url_to_json(raw)
            elif action == "格式化输出":
                data = auto_parse(raw)
                result = data
            elif action == "压缩输出":
                data = auto_parse(raw)
                formatted = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
                output_text.delete("1.0", tk.END)
                output_text.insert(tk.END, formatted)
                return
            elif action == "复制结果":
                result_text = output_text.get("1.0", tk.END).strip()
                if not result_text:
                    messagebox.showwarning("提示", "输出为空，无法复制")
                    return
                root.clipboard_clear()
                root.clipboard_append(result_text)
                messagebox.showinfo("成功", "已复制到剪贴板")
                return
            elif action == "保存结果":
                result_text = output_text.get("1.0", tk.END).strip()
                if not result_text:
                    messagebox.showwarning("提示", "输出为空，无法保存")
                    return
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
                )
                if save_path:
                    with open(save_path, 'w', encoding='utf-8') as f:
                        f.write(result_text)
                    messagebox.showinfo("成功", f"已保存到：{save_path}")
                return
            elif action == "生成模板":
                try:
                    schema = json.loads(raw)
                    result = converter.generate_template(schema)
                except Exception as e:
                    messagebox.showerror("模板生成失败", str(e))
                    return

            if result is not None:
                formatted = json.dumps(result, indent=2, ensure_ascii=False)
                output_text.delete("1.0", tk.END)
                output_text.insert(tk.END, formatted)
                highlight_json(output_text)
                # 更新树形视图
                tree_view.delete(*tree_view.get_children())
                tree_view.load(result)

        except Exception as e:
            messagebox.showerror("操作失败", str(e))
        finally:
            combo.set("请选择")  # 重置下拉菜单

    combo.bind("<<ComboboxSelected>>", on_action_selected)

    # 添加解析按钮
    parse_button = ttk.Button(action_frame, text="解析", command=parse_and_show)
    parse_button.pack(side=tk.LEFT, padx=5)

    # 在 action_frame 中添加数据增强功能
    enhance_button = ttk.Button(action_frame, text="增强数据", command=lambda: show_enhance_dialog(root, input_text, output_text, tree_view))
    enhance_button.pack(side=tk.LEFT, padx=5)

    # 在 action_frame 中添加 JavaScript 输出按钮
    js_button = ttk.Button(action_frame, text="转为JS", command=lambda: show_js_dialog(root, input_text, output_text))
    js_button.pack(side=tk.LEFT, padx=5)

    transform_button = ttk.Button(action_frame, text="数据转换", command=lambda: show_transform_dialog(root, input_text, output_text, tree_view))
    transform_button.pack(side=tk.LEFT, padx=5)

    def show_enhance_dialog(parent, input_text, output_text, tree_view):
        dialog = tk.Toplevel(parent)
        dialog.title("数据增强")
        dialog.geometry("600x400")
        dialog.transient(parent)
        dialog.grab_set()

        # 说明文本
        tk.Label(dialog, text="请输入要添加或修改的字段配置，每行一个，格式：字段名=类型或固定值", anchor="w").pack(fill=tk.X, padx=10, pady=5)
        tk.Label(dialog, text="类型示例：string, number, date, email 等", anchor="w").pack(fill=tk.X, padx=10)
        tk.Label(dialog, text="固定值示例：=固定的值（以等号开头）", anchor="w").pack(fill=tk.X, padx=10)
        
        # 配置输入区域
        config_text = scrolledtext.ScrolledText(dialog, height=10)
        config_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 预设模板按钮框架
        templates_frame = ttk.LabelFrame(dialog, text="常用模板")
        templates_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 预设模板
        templates = {
            "添加ID": "id=id\nstatus=status\ncreated_at=datetime",
            "添加用户信息": "username=name\nemail=email\nphone=phone\navatar=avatar",
            "添加地址信息": "province=province\ncity=city\naddress=address",
            "添加随机标记": "tags=[string]\nis_active=boolean\ntype=[\"normal\", \"vip\", \"svip\"]"
        }
        
        def apply_template(template):
            config_text.delete("1.0", tk.END)
            config_text.insert(tk.END, templates[template])
        
        for template_name in templates:
            ttk.Button(templates_frame, text=template_name, 
                      command=lambda t=template_name: apply_template(t)).pack(side=tk.LEFT, padx=5, pady=5)
        
        def apply_enhancements():
            try:
                # 获取原始数据
                raw = input_text.get("1.0", tk.END).strip()
                if not raw:
                    messagebox.showwarning("提示", "请先输入数据")
                    return
                
                # 解析原始数据
                data = auto_parse(raw)
                
                # 解析配置
                config_raw = config_text.get("1.0", tk.END).strip()
                if not config_raw:
                    messagebox.showwarning("提示", "请输入配置")
                    return
                
                enhancements = {}
                for line in config_raw.split('\n'):
                    if '=' not in line:
                        continue
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        enhancements[key] = value
                
                # 应用增强
                result = converter.enhance_data(data, enhancements)
                
                # 更新输出
                formatted = json.dumps(result, indent=2, ensure_ascii=False)
                output_text.delete("1.0", tk.END)
                output_text.insert(tk.END, formatted)
                highlight_json(output_text)
                
                # 更新树形视图
                tree_view.delete(*tree_view.get_children())
                tree_view.load(result)
                
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("错误", str(e))
        
        # 按钮区域
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="应用", command=apply_enhancements).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def show_js_dialog(parent, input_text, output_text):
        dialog = tk.Toplevel(parent)
        dialog.title("转换为 JavaScript")
        dialog.geometry("600x500")
        dialog.transient(parent)
        dialog.grab_set()

        # 选项框架
        options_frame = ttk.LabelFrame(dialog, text="输出选项")
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        # 变量名输入
        name_frame = ttk.Frame(options_frame)
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(name_frame, text="变量名:").pack(side=tk.LEFT)
        name_var = tk.StringVar(value="data")
        ttk.Entry(name_frame, textvariable=name_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 格式选择
        format_frame = ttk.Frame(options_frame)
        format_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(format_frame, text="格式:").pack(side=tk.LEFT)
        format_var = tk.StringVar(value="const")
        formats = [
            ("const 声明", "const"),
            ("let 声明", "let"),
            ("var 声明", "var"),
            ("export const", "export"),
            ("module.exports", "module.exports"),
            ("类静态属性", "class"),
            ("TypeScript", "typescript")
        ]
        for text, value in formats:
            ttk.Radiobutton(format_frame, text=text, value=value, variable=format_var).pack(side=tk.LEFT, padx=5)

        # 预览区域
        preview_frame = ttk.LabelFrame(dialog, text="预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        preview_text = scrolledtext.ScrolledText(preview_frame)
        preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def update_preview():
            try:
                # 获取输入数据
                raw = input_text.get("1.0", tk.END).strip()
                if not raw:
                    messagebox.showwarning("提示", "请先输入数据")
                    return
                
                # 解析数据
                data = auto_parse(raw)
                
                # 转换为 JavaScript
                result = converter.to_javascript(
                    data,
                    format_type=format_var.get(),
                    variable_name=name_var.get()
                )
                
                # 更新预览
                preview_text.delete("1.0", tk.END)
                preview_text.insert(tk.END, result)
                
            except Exception as e:
                messagebox.showerror("错误", str(e))

        # 更新按钮
        ttk.Button(options_frame, text="更新预览", command=update_preview).pack(pady=5)

        # 按钮区域
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def apply_js():
            preview_content = preview_text.get("1.0", tk.END).strip()
            if preview_content:
                output_text.delete("1.0", tk.END)
                output_text.insert(tk.END, preview_content)
                dialog.destroy()

        ttk.Button(button_frame, text="应用", command=apply_js).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        # 初始预览
        update_preview()

    def show_transform_dialog(parent, input_text, output_text, tree_view):
        dialog = tk.Toplevel(parent)
        dialog.title("数据转换")
        dialog.geometry("800x600")
        dialog.transient(parent)
        dialog.grab_set()

        # 转换步骤列表框架
        steps_frame = ttk.LabelFrame(dialog, text="转换步骤")
        steps_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 步骤列表
        steps_list = tk.Listbox(steps_frame, height=6)
        steps_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 步骤操作按钮
        steps_buttons = ttk.Frame(steps_frame)
        steps_buttons.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        transforms = []  # 存储转换步骤

        def add_step():
            dialog = tk.Toplevel(parent)
            dialog.title("添加转换步骤")
            dialog.geometry("400x300")
            dialog.transient(parent)
            dialog.grab_set()

            # 转换类型选择
            type_frame = ttk.LabelFrame(dialog, text="转换类型")
            type_frame.pack(fill=tk.X, padx=10, pady=5)

            type_var = tk.StringVar(value="group")
            types = [
                ("按字段分组", "group"),
                ("过滤数据", "filter"),
                ("排序", "sort"),
                ("字段映射", "map"),
                ("展平数组", "flatten"),
                ("聚合计算", "aggregate")
            ]
            for text, value in types:
                ttk.Radiobutton(type_frame, text=text, value=value, variable=type_var).pack(anchor=tk.W)

            # 参数配置框架
            params_frame = ttk.LabelFrame(dialog, text="参数配置")
            params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            params_text = scrolledtext.ScrolledText(params_frame, height=6)
            params_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            def update_params_hint():
                transform_type = type_var.get()
                hint = ""
                if transform_type == "group":
                    hint = '{\n  "field": "要分组的字段名"\n}'
                elif transform_type == "filter":
                    hint = '{\n  "condition": {\n    "字段名": {"op": "值"},\n    "age": {"gt": 18}\n  }\n}'
                elif transform_type == "sort":
                    hint = '{\n  "field": "要排序的字段名",\n  "reverse": false\n}'
                elif transform_type == "map":
                    hint = '{\n  "mapping": {\n    "旧字段名": "新字段名"\n  }\n}'
                elif transform_type == "flatten":
                    hint = '{}'
                elif transform_type == "aggregate":
                    hint = '{\n  "group_by": ["分组字段1", "分组字段2"],\n  "metrics": [\n    {\n      "field": "计算字段",\n      "op": "sum",\n      "as": "结果字段名"\n    }\n  ]\n}'
                
                params_text.delete("1.0", tk.END)
                params_text.insert(tk.END, hint)

            type_var.trace("w", lambda *args: update_params_hint())
            update_params_hint()

            def add_transform():
                try:
                    params = json.loads(params_text.get("1.0", tk.END))
                    transform = {
                        "type": type_var.get(),
                        "params": params
                    }
                    transforms.append(transform)
                    steps_list.insert(tk.END, f"{dict(types)[transform['type']]} - {json.dumps(params, ensure_ascii=False)}")
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("错误", str(e))

            # 按钮区域
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            ttk.Button(button_frame, text="添加", command=add_transform).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        def remove_step():
            selection = steps_list.curselection()
            if not selection:
                return
            
            index = selection[0]
            steps_list.delete(index)
            transforms.pop(index)

        def move_step(direction):
            selection = steps_list.curselection()
            if not selection:
                return
            
            index = selection[0]
            if direction == "up" and index > 0:
                # 上移
                transforms[index], transforms[index-1] = transforms[index-1], transforms[index]
                text = steps_list.get(index)
                steps_list.delete(index)
                steps_list.insert(index-1, text)
                steps_list.selection_set(index-1)
            elif direction == "down" and index < steps_list.size()-1:
                # 下移
                transforms[index], transforms[index+1] = transforms[index+1], transforms[index]
                text = steps_list.get(index)
                steps_list.delete(index)
                steps_list.insert(index+1, text)
                steps_list.selection_set(index+1)

        ttk.Button(steps_buttons, text="添加", command=add_step).pack(fill=tk.X, pady=2)
        ttk.Button(steps_buttons, text="删除", command=remove_step).pack(fill=tk.X, pady=2)
        ttk.Button(steps_buttons, text="上移", command=lambda: move_step("up")).pack(fill=tk.X, pady=2)
        ttk.Button(steps_buttons, text="下移", command=lambda: move_step("down")).pack(fill=tk.X, pady=2)

        # 预览区域
        preview_frame = ttk.LabelFrame(dialog, text="预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        preview_text = scrolledtext.ScrolledText(preview_frame)
        preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def update_preview():
            try:
                # 获取输入数据
                raw = input_text.get("1.0", tk.END).strip()
                if not raw:
                    messagebox.showwarning("提示", "请先输入数据")
                    return
                
                # 解析数据
                data = auto_parse(raw)
                
                # 应用转换
                result = converter.transform_data(data, transforms)
                
                # 更新预览
                formatted = json.dumps(result, indent=2, ensure_ascii=False)
                preview_text.delete("1.0", tk.END)
                preview_text.insert(tk.END, formatted)
                
            except Exception as e:
                messagebox.showerror("错误", str(e))

        # 更新按钮
        ttk.Button(steps_frame, text="更新预览", command=update_preview).pack(pady=5)

        # 按钮区域
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def apply_transform():
            preview_content = preview_text.get("1.0", tk.END).strip()
            if preview_content:
                output_text.delete("1.0", tk.END)
                output_text.insert(tk.END, preview_content)
                # 更新树形视图
                tree_view.delete(*tree_view.get_children())
                tree_view.load(json.loads(preview_content))
                dialog.destroy()

        ttk.Button(button_frame, text="应用", command=apply_transform).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    return input_text, output_text, find_entry, replace_entry, jsonpath_entry, nav_label
