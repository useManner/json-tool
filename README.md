# 多格式数据解析与转换工具

这是一个基于 Python Tkinter 的 GUI 工具，支持 JSON、YAML、XML、CSV 和 URL 参数格式的数据解析、转换和格式化。

## 功能特点

- 多格式自动解析（JSON、YAML、XML、CSV、URL参数）
- 支持查找替换功能
- JSONPath 查询，方便快速提取数据
- 格式化、压缩 JSON 输出
- 复制结果、保存到文件
- 导出 Excel 文件
- 数据模板生成
- 支持暗黑模式切换
- JSON 树形可视化

## 依赖安装

```bash
pip install jsonpath-ng pyyaml xmltodict

```

## 使用说明

### 基本操作

1. **数据解析**：
   - 将数据粘贴到输入区域
   - 点击"解析"按钮
   - 解析结果会显示在输出区域和树形视图中

2. **格式转换**：
   - 从下拉菜单选择需要的转换格式
   - 支持：XML转JSON、YAML转JSON、CSV转JSON、URL参数转JSON等

3. **查找替换**：
   - 使用查找框输入关键字
   - 支持替换和全部替换
   - 支持导航到下一个匹配项

4. **JSONPath查询**：
   - 在 JSONPath 输入框中输入表达式
   - 例如：`$.store.book[*].author`

### 模板生成功能

支持两种模板生成方式：

#### 1. 简化格式（推荐）

直接使用类型名称或示例值：

```json
{
  "id": "id",
  "name": "name",
  "email": "email",
  "created_at": "datetime",
  "tags": ["string"],
  "settings": {
    "notifications": "boolean",
    "theme": ["light", "dark", "auto"]
  }
}
```

#### 支持的类型

1. **基本类型**：
   - `string`: 随机字符串
   - `number`/`int`/`integer`: 随机数字
   - `float`: 随机浮点数
   - `boolean`: 随机布尔值
   - `null`: null 值

2. **日期时间**：
   - `date`: 日期（YYYY-MM-DD）
   - `time`: 时间（HH:mm:ss）
   - `datetime`: 日期时间（ISO 格式）

3. **个人信息**：
   - `name`: 随机中文名
   - `email`: 随机邮箱
   - `phone`/`mobile`: 随机手机号
   - `avatar`: 随机头像URL

4. **地址信息**：
   - `address`: 随机地址
   - `city`: 随机城市
   - `province`: 随机省份

5. **其他类型**：
   - `id`: 随机ID（1-1000）
   - `guid`/`uuid`: 随机UUID
   - `url`: 随机URL
   - `image`: 随机图片URL
   - `ip`: 随机IP地址
   - `status`: 随机状态
   - `color`: 随机颜色
   - `text`: 随机文本段落

6. **复合类型**：
   - 数组：使用 `[类型]` 格式，如 `["string"]`
   - 对象：使用 `{}` 格式
   - 枚举：直接使用数组，如 `["light", "dark", "auto"]`

#### 2. 标准 JSON Schema 格式

也支持完整的 JSON Schema 格式：

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "name": {
      "type": "string"
    },
    "email": {
      "type": "string",
      "format": "email"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "maxItems": 3
    }
  },
  "required": ["id", "name", "email"]
}
```

### 使用技巧

1. **快速格式化**：
   - 使用"格式化输出"功能美化 JSON
   - 使用"压缩输出"功能移除空白字符

2. **数据导出**：
   - 可以将结果复制到剪贴板
   - 可以保存为文件
   - 支持导出为 Excel 格式

3. **树形视图操作**：
   - 双击节点复制值
   - 右键菜单支持复制值和路径
   - 可展开/折叠节点查看数据结构

4. **暗黑模式**：
   - 点击暗黑模式按钮切换界面主题
   - 自动保存主题偏好

## 注意事项

1. 大文件处理时可能需要等待
2. 复杂的 JSON 数据建议使用树形视图浏览
3. 生成模板时，建议使用简化格式，更直观且易于维护
