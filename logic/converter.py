import json
import csv
import io
import urllib.parse
import xmltodict
import yaml
import pandas as pd
import random
import datetime
import uuid

class Converter:
    def __init__(self):
        self.type_generators = {
            'string': self._generate_string,
            'number': self._generate_number,
            'integer': self._generate_integer,
            'boolean': self._generate_boolean,
            'array': self._generate_array,
            'object': self._generate_object,
            'null': self._generate_null
        }

    def xml_to_json(self, xml_str):
        return xmltodict.parse(xml_str)

    def yaml_to_json(self, yaml_str):
        return yaml.safe_load(yaml_str)

    def csv_to_json(self, csv_str):
        """将 CSV 字符串转换为 JSON 数据
        支持 Excel 复制的表格数据（制表符分隔）
        """
        try:
            # 首先尝试标准 CSV 格式
            return list(csv.DictReader(io.StringIO(csv_str)))
        except Exception:
            try:
                # 尝试处理 Excel 复制的数据（制表符分隔）
                lines = csv_str.strip().split('\n')
                if not lines:
                    return []
                
                # 处理表头
                headers = lines[0].strip().split('\t')
                headers = [h.strip() for h in headers if h.strip()]
                
                # 处理数据行
                result = []
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    values = line.strip().split('\t')
                    # 确保值的数量与表头一致
                    values = values[:len(headers)]
                    while len(values) < len(headers):
                        values.append("")
                    
                    row = {}
                    for i, header in enumerate(headers):
                        value = values[i].strip()
                        # 尝试转换数值类型
                        try:
                            if '.' in value:
                                row[header] = float(value)
                            elif value.isdigit():
                                row[header] = int(value)
                            else:
                                row[header] = value
                        except:
                            row[header] = value
                    result.append(row)
                return result
            except Exception as e:
                raise ValueError(f"无法解析表格数据: {str(e)}")

    def url_to_json(self, url_str):
        return dict(urllib.parse.parse_qsl(url_str))

    def excel_to_json(self, file_path):
        df = pd.read_excel(file_path)
        return json.loads(df.to_json(orient='records'))

    def json_to_excel(self, json_data, save_path):
        df = pd.DataFrame(json_data)
        df.to_excel(save_path, index=False)

    def enhance_data(self, data, enhancements):
        """增强数据，添加自定义字段或修改现有字段
        
        Args:
            data: 原始数据（列表或字典）
            enhancements: 增强配置，格式如：
                {
                    "新字段": "类型或固定值",
                    "现有字段": "新的固定值或类型"
                }
        """
        if isinstance(data, list):
            return [self.enhance_data(item, enhancements) for item in data]
        
        if isinstance(data, dict):
            result = data.copy()
            for key, value_type in enhancements.items():
                if isinstance(value_type, str) and value_type.startswith("="):
                    # 固定值，直接赋值
                    result[key] = value_type[1:]
                else:
                    # 使用模板生成器生成值
                    result[key] = self._generate_simple_value(value_type)
            return result
        
        return data

    def auto_to_json(self, raw_text):
        """自动检测并转换数据格式"""
        raw_text = raw_text.strip()
        
        # 检查是否是 Excel 复制的表格数据
        if '\t' in raw_text and '\n' in raw_text:
            try:
                return self.csv_to_json(raw_text)
            except Exception:
                pass

        # 其他格式的检查...
        try:
            return json.loads(raw_text)
        except Exception:
            pass

        try:
            return yaml.safe_load(raw_text)
        except Exception:
            pass

        try:
            return xmltodict.parse(raw_text)
        except Exception:
            pass

        if ',' in raw_text and '\n' in raw_text:
            try:
                return self.csv_to_json(raw_text)
            except Exception:
                pass

        if '=' in raw_text:
            try:
                return self.url_to_json(raw_text)
            except Exception:
                pass

        raise ValueError("无法识别输入格式")

    def generate_template(self, schema):
        """根据模板生成示例数据
        
        支持两种格式：
        1. 简化格式：直接使用值的类型名或示例值
           {
             "name": "string",
             "age": "number",
             "email": "email",
             "tags": ["string"],
             "settings": {
               "theme": ["light", "dark"]
             }
           }
        
        2. 标准 JSON Schema 格式（保持原有功能）
        
        Args:
            schema: 模板对象
            
        Returns:
            生成的示例数据
        """
        # 如果是标准 JSON Schema，使用原有逻辑
        if isinstance(schema, dict) and schema.get('type') == 'object' and 'properties' in schema:
            return self._generate_from_json_schema(schema)
            
        # 否则使用简化格式处理
        return self._generate_from_simple_schema(schema)

    def _generate_from_json_schema(self, schema):
        """使用原有的 JSON Schema 处理逻辑"""
        if not isinstance(schema, dict):
            return schema

        if 'type' not in schema:
            if 'properties' in schema:
                return self._generate_object(schema)
            elif 'items' in schema:
                return self._generate_array(schema)
            else:
                return schema

        type_name = schema['type']
        generator = self.type_generators.get(type_name)
        if generator:
            return generator(schema)
        return None

    def _generate_from_simple_schema(self, schema):
        """处理简化格式的模板"""
        if isinstance(schema, str):
            return self._generate_simple_value(schema)
        elif isinstance(schema, list):
            if not schema:
                return []
            # 生成1-3个元素
            count = random.randint(1, 3)
            return [self._generate_from_simple_schema(schema[0]) for _ in range(count)]
        elif isinstance(schema, dict):
            return {k: self._generate_from_simple_schema(v) for k, v in schema.items()}
        return schema

    def _generate_simple_value(self, type_str):
        """根据类型字符串生成值"""
        type_map = {
            "string": lambda: random.choice(["张三", "李四", "王五", "赵六"]),
            "name": lambda: random.choice(["李雷", "韩梅梅", "张三丰", "王小明"]),
            "text": lambda: random.choice([
                "这是一段示例文本",
                "用于测试的文字内容",
                "Hello World",
                "示例描述信息"
            ]),
            "number": lambda: random.randint(1, 100),
            "int": lambda: random.randint(1, 100),
            "integer": lambda: random.randint(1, 100),
            "float": lambda: round(random.uniform(0, 100), 2),
            "boolean": lambda: random.choice([True, False]),
            "null": lambda: None,
            "date": lambda: datetime.date.today().isoformat(),
            "time": lambda: datetime.datetime.now().time().isoformat()[:8],
            "datetime": lambda: datetime.datetime.now().isoformat(),
            "email": lambda: f"user{random.randint(1,100)}@example.com",
            "url": lambda: f"https://example.com/page/{random.randint(1, 100)}",
            "image": lambda: f"https://picsum.photos/id/{random.randint(1,1000)}/200/300",
            "avatar": lambda: f"https://i.pravatar.cc/150?img={random.randint(1,70)}",
            "phone": lambda: f"1{random.choice(['3','5','7','8','9'])}{random.randint(100000000,999999999)}",
            "mobile": lambda: f"1{random.choice(['3','5','7','8','9'])}{random.randint(100000000,999999999)}",
            "address": lambda: random.choice([
                "北京市朝阳区三里屯街道",
                "上海市浦东新区张江路",
                "广州市天河区体育西路",
                "深圳市南山区科技园"
            ]),
            "city": lambda: random.choice([
                "北京", "上海", "广州", "深圳",
                "杭州", "南京", "成都", "武汉"
            ]),
            "province": lambda: random.choice([
                "北京", "上海", "广东", "江苏",
                "浙江", "四川", "湖北", "福建"
            ]),
            "id": lambda: random.randint(1, 1000),
            "guid": lambda: str(uuid.uuid4()),
            "uuid": lambda: str(uuid.uuid4()),
            "status": lambda: random.choice(["active", "inactive", "pending", "deleted"]),
            "color": lambda: random.choice(["red", "blue", "green", "yellow", "purple"]),
            "ip": lambda: f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        }
        
        # 如果是枚举值（格式如：["a", "b", "c"]），直接从中随机选择
        try:
            enum_values = json.loads(type_str)
            if isinstance(enum_values, list):
                return random.choice(enum_values)
        except:
            pass
            
        # 使用预定义的类型生成器，如果没有对应的类型，返回原字符串
        return type_map.get(type_str.lower(), lambda: type_str)()

    def _generate_string(self, schema):
        """生成字符串类型的示例数据"""
        if 'enum' in schema:
            return random.choice(schema['enum'])
        if 'format' in schema:
            format_type = schema['format']
            if format_type == 'date-time':
                return datetime.datetime.now().isoformat()
            elif format_type == 'date':
                return datetime.date.today().isoformat()
            elif format_type == 'time':
                return datetime.datetime.now().time().isoformat()
            elif format_type == 'email':
                return 'user@example.com'
            elif format_type == 'uri':
                return 'http://example.com'
        if 'pattern' in schema:
            return f"符合正则 {schema['pattern']} 的字符串"
        return "示例字符串"

    def _generate_number(self, schema):
        """生成数字类型的示例数据"""
        if 'enum' in schema:
            return random.choice(schema['enum'])
        minimum = schema.get('minimum', 0)
        maximum = schema.get('maximum', 100)
        if 'multipleOf' in schema:
            multiple = schema['multipleOf']
            return (random.randint(minimum // multiple, maximum // multiple) * multiple)
        return random.uniform(minimum, maximum)

    def _generate_integer(self, schema):
        """生成整数类型的示例数据"""
        if 'enum' in schema:
            return random.choice(schema['enum'])
        minimum = schema.get('minimum', 0)
        maximum = schema.get('maximum', 100)
        return random.randint(minimum, maximum)

    def _generate_boolean(self, schema):
        """生成布尔类型的示例数据"""
        return random.choice([True, False])

    def _generate_array(self, schema):
        """生成数组类型的示例数据"""
        if not schema.get('items'):
            return []
        min_items = schema.get('minItems', 1)
        max_items = schema.get('maxItems', 3)
        length = random.randint(min_items, max_items)
        items_schema = schema['items']
        return [self.generate_template(items_schema) for _ in range(length)]

    def _generate_object(self, schema):
        """生成对象类型的示例数据"""
        result = {}
        if 'properties' not in schema:
            return result
        
        required = schema.get('required', [])
        for prop_name, prop_schema in schema['properties'].items():
            if prop_name in required or random.random() > 0.5:
                result[prop_name] = self.generate_template(prop_schema)
        return result

    def _generate_null(self, schema):
        """生成 null 类型的示例数据"""
        return None

    def to_javascript(self, data, format_type="const", variable_name="data"):
        """将数据转换为 JavaScript 格式
        
        Args:
            data: 要转换的数据
            format_type: 输出格式类型
                - const: 常量声明
                - let: let 声明
                - var: var 声明
                - export: export const 声明
                - module.exports: CommonJS 格式
                - class: 类属性格式
                - typescript: TypeScript 接口和数据
            variable_name: 变量名称
        """
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        if format_type == "const":
            return f"const {variable_name} = {json_str};"
        elif format_type == "let":
            return f"let {variable_name} = {json_str};"
        elif format_type == "var":
            return f"var {variable_name} = {json_str};"
        elif format_type == "export":
            return f"export const {variable_name} = {json_str};"
        elif format_type == "module.exports":
            return f"module.exports = {json_str};"
        elif format_type == "class":
            return f"class {variable_name.capitalize()} {{\n  static data = {json_str};\n}}"
        elif format_type == "typescript":
            # 生成 TypeScript 接口
            if isinstance(data, list) and len(data) > 0:
                sample = data[0]
                interface = self._generate_typescript_interface(sample, variable_name.capitalize())
                return f"{interface}\n\nexport const {variable_name}: {variable_name.capitalize()}[] = {json_str};"
            elif isinstance(data, dict):
                interface = self._generate_typescript_interface(data, variable_name.capitalize())
                return f"{interface}\n\nexport const {variable_name}: {variable_name.capitalize()} = {json_str};"
            else:
                return f"export const {variable_name} = {json_str};"
        else:
            raise ValueError(f"不支持的格式类型: {format_type}")

    def _generate_typescript_interface(self, data, interface_name):
        """生成 TypeScript 接口定义"""
        if not isinstance(data, dict):
            return ""
        
        lines = [f"interface {interface_name} {{"]
        
        for key, value in data.items():
            if isinstance(value, dict):
                # 递归生成嵌套接口
                nested_interface = self._generate_typescript_interface(value, f"{interface_name}{key.capitalize()}")
                lines.append(nested_interface)
                lines.append(f"  {key}: {interface_name}{key.capitalize()};")
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    # 数组元素是对象
                    nested_interface = self._generate_typescript_interface(value[0], f"{interface_name}{key.capitalize()}")
                    lines.append(nested_interface)
                    lines.append(f"  {key}: {interface_name}{key.capitalize()}[];")
                else:
                    # 简单类型数组
                    type_name = self._get_typescript_type(value[0] if value else None)
                    lines.append(f"  {key}: {type_name}[];")
            else:
                type_name = self._get_typescript_type(value)
                lines.append(f"  {key}: {type_name};")
        
        lines.append("}")
        return "\n".join(lines)

    def _get_typescript_type(self, value):
        """获取 TypeScript 类型名称"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int) or isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif value is None:
            return "null"
        else:
            return "any"

    def transform_data(self, data, transforms):
        """转换数据结构
        
        Args:
            data: 原始数据
            transforms: 转换配置列表，每个配置是一个字典：
                {
                    "type": "转换类型",
                    "params": {} # 转换参数
                }
        """
        result = data
        for transform in transforms:
            transform_type = transform.get("type", "")
            params = transform.get("params", {})
            
            if transform_type == "group":
                # 按字段分组
                field = params.get("field")
                if not field:
                    continue
                result = self._group_by_field(result, field)
            
            elif transform_type == "filter":
                # 过滤数据
                condition = params.get("condition", {})
                result = self._filter_data(result, condition)
            
            elif transform_type == "sort":
                # 排序
                field = params.get("field")
                reverse = params.get("reverse", False)
                if not field:
                    continue
                result = self._sort_data(result, field, reverse)
            
            elif transform_type == "map":
                # 字段映射
                mapping = params.get("mapping", {})
                result = self._map_fields(result, mapping)
            
            elif transform_type == "flatten":
                # 展平嵌套数组
                result = self._flatten_array(result)
            
            elif transform_type == "aggregate":
                # 聚合计算
                group_by = params.get("group_by")
                metrics = params.get("metrics", [])
                result = self._aggregate_data(result, group_by, metrics)
        
        return result

    def _group_by_field(self, data, field):
        """按字段分组"""
        if not isinstance(data, list):
            return data
        
        groups = {}
        for item in data:
            key = item.get(field)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups

    def _filter_data(self, data, condition):
        """过滤数据"""
        if not isinstance(data, list):
            return data
        
        def match_condition(item, cond):
            for field, value in cond.items():
                if isinstance(value, dict):
                    # 支持运算符
                    for op, val in value.items():
                        if op == "eq" and item.get(field) != val:
                            return False
                        elif op == "ne" and item.get(field) == val:
                            return False
                        elif op == "gt" and not (isinstance(item.get(field), (int, float)) and item.get(field) > val):
                            return False
                        elif op == "lt" and not (isinstance(item.get(field), (int, float)) and item.get(field) < val):
                            return False
                        elif op == "in" and item.get(field) not in val:
                            return False
                else:
                    # 简单相等判断
                    if item.get(field) != value:
                        return False
            return True
        
        return [item for item in data if match_condition(item, condition)]

    def _sort_data(self, data, field, reverse=False):
        """排序数据"""
        if not isinstance(data, list):
            return data
        
        return sorted(data, key=lambda x: x.get(field, ""), reverse=reverse)

    def _map_fields(self, data, mapping):
        """字段映射"""
        if isinstance(data, list):
            return [self._map_fields(item, mapping) for item in data]
        
        if isinstance(data, dict):
            result = {}
            for old_key, new_key in mapping.items():
                if old_key in data:
                    result[new_key] = data[old_key]
            return result
        
        return data

    def _flatten_array(self, data):
        """展平嵌套数组"""
        if not isinstance(data, list):
            return data
        
        result = []
        for item in data:
            if isinstance(item, list):
                result.extend(self._flatten_array(item))
            else:
                result.append(item)
        return result

    def _aggregate_data(self, data, group_by, metrics):
        """聚合计算"""
        if not isinstance(data, list) or not group_by:
            return data
        
        groups = {}
        for item in data:
            key = tuple(item.get(field) for field in group_by)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        
        result = []
        for key, group in groups.items():
            row = {field: value for field, value in zip(group_by, key)}
            
            for metric in metrics:
                field = metric.get("field")
                op = metric.get("op", "sum")
                as_field = metric.get("as", f"{op}_{field}")
                
                values = [item.get(field, 0) for item in group]
                if op == "sum":
                    row[as_field] = sum(values)
                elif op == "avg":
                    row[as_field] = sum(values) / len(values) if values else 0
                elif op == "count":
                    row[as_field] = len(values)
                elif op == "max":
                    row[as_field] = max(values) if values else None
                elif op == "min":
                    row[as_field] = min(values) if values else None
            
            result.append(row)
        
        return result
