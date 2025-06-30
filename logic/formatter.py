import json

class Formatter:
    def format(self, data, indent=4, sort_keys=False):
        """格式化 JSON 数据
        
        Args:
            data: 要格式化的数据
            indent: 缩进空格数
            sort_keys: 是否按键排序
        """
        return json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=sort_keys)

    def minify(self, data):
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)

    def validate(self, s):
        """验证 JSON 字符串的有效性
        
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            json.loads(s)
            return True, ""
        except Exception as e:
            return False, str(e)

    def format_with_options(self, data, **options):
        """使用自定义选项格式化 JSON 数据
        
        Args:
            data: 要格式化的数据
            **options: 格式化选项
                - indent: 缩进空格数
                - sort_keys: 是否按键排序
                - ensure_ascii: 是否确保 ASCII 输出
                - separators: 分隔符元组 (item_separator, key_separator)
        """
        return json.dumps(data, **options)

    def pretty_print(self, data):
        """美化打印，适用于控制台输出
        
        - 添加颜色
        - 添加类型提示
        - 格式化时间戳
        """
        formatted = self.format(data, indent=2)
        # 这里可以添加 ANSI 颜色代码等美化处理
        return formatted
