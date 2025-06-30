import tkinter as tk
from tkinter import ttk
import json

class JSONTreeView(ttk.Treeview):
    def __init__(self, master):
        super().__init__(master, columns=("value", "type"), show="tree headings")
        self.heading("value", text="值")
        self.heading("type", text="类型")
        self.column("value", width=300)
        self.column("type", width=100)
        
        # 绑定事件
        self.bind("<Double-1>", self.on_double_click)
        self.bind("<Button-3>", self.on_right_click)
        
        # 右键菜单
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="复制值", command=self._copy_value)
        self.context_menu.add_command(label="复制路径", command=self._copy_path)
        
        # 保存数据引用
        self.data = None
        
        # 设置标签样式
        self.tag_configure("dict", foreground="blue")
        self.tag_configure("list", foreground="green")
        self.tag_configure("string", foreground="red")
        self.tag_configure("number", foreground="purple")
        self.tag_configure("boolean", foreground="orange")
        self.tag_configure("null", foreground="gray")

    def load(self, data):
        """加载 JSON 数据到树形视图"""
        try:
            # 清除现有数据
            self.delete(*self.get_children())
            self.data = data
            # 添加新数据
            self._insert_node("", data)
        except Exception as e:
            print(f"Error loading data into tree view: {e}")

    def _insert_node(self, parent, data, key=None):
        """递归插入节点"""
        try:
            if isinstance(data, dict):
                node = self.insert(parent, "end", text=str(key) if key is not None else "Object",
                                values=("", "object"), tags=("dict",))
                for k, v in data.items():
                    self._insert_node(node, v, k)
                return node
            elif isinstance(data, list):
                node = self.insert(parent, "end", text=str(key) if key is not None else "Array",
                                values=(f"[{len(data)} items]", "array"), tags=("list",))
                for i, item in enumerate(data):
                    self._insert_node(node, item, i)
                return node
            else:
                # 处理基本类型
                value = str(data) if data is not None else "null"
                type_name = type(data).__name__ if data is not None else "null"
                tags = (type_name,)
                return self.insert(parent, "end", text=str(key) if key is not None else "",
                                values=(value, type_name), tags=tags)
        except Exception as e:
            print(f"Error inserting node: {e}")
            return None

    def on_double_click(self, event):
        """双击节点时复制值"""
        try:
            item = self.selection()[0]
            values = self.item(item)["values"]
            if values and values[0]:
                self.clipboard_clear()
                self.clipboard_append(values[0])
        except Exception as e:
            print(f"Error on double click: {e}")

    def on_right_click(self, event):
        """显示右键菜单"""
        try:
            item = self.identify_row(event.y)
            if item:
                self.selection_set(item)
                self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error on right click: {e}")

    def _copy_value(self):
        """复制选中节点的值"""
        try:
            item = self.selection()[0]
            values = self.item(item)["values"]
            if values and values[0]:
                self.clipboard_clear()
                self.clipboard_append(values[0])
        except Exception as e:
            print(f"Error copying value: {e}")

    def _copy_path(self):
        """复制选中节点的 JSON 路径"""
        try:
            item = self.selection()[0]
            path = self.get_json_path(item)
            if path:
                self.clipboard_clear()
                self.clipboard_append(path)
        except Exception as e:
            print(f"Error copying path: {e}")

    def get_json_path(self, item):
        """获取节点的 JSON 路径"""
        try:
            path = []
            while item:
                parent = self.parent(item)
                if not parent:
                    break
                text = self.item(item)["text"]
                if str(text).isdigit():
                    path.append(f"[{text}]")
                else:
                    path.append(f".{text}" if text else "")
                item = parent
            path.reverse()
            return "$" + "".join(path)
        except Exception as e:
            print(f"Error getting JSON path: {e}")
            return ""

    def clear(self):
        """清除树形视图的所有数据"""
        try:
            self.delete(*self.get_children())
            self.data = None
        except Exception as e:
            print(f"Error clearing tree view: {e}")

