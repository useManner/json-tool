import json
class Formatter:
    def format(self, data): return json.dumps(data, indent=4, ensure_ascii=False)
    def minify(self, data): return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    def validate(self, s):
        try: json.loads(s); return True, ""
        except Exception as e: return False, str(e)
