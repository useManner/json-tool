import json
import csv
import io
import urllib.parse
import xmltodict
import yaml
import pandas as pd

class Converter:

    def xml_to_json(self, xml_str):
        return xmltodict.parse(xml_str)

    def yaml_to_json(self, yaml_str):
        return yaml.safe_load(yaml_str)

    def csv_to_json(self, csv_str):
        return list(csv.DictReader(io.StringIO(csv_str)))

    def url_to_json(self, url_str):
        return dict(urllib.parse.parse_qsl(url_str))

    def excel_to_json(self, file_path):
        df = pd.read_excel(file_path)
        return json.loads(df.to_json(orient='records'))

    def json_to_excel(self, json_data, save_path):
        df = pd.DataFrame(json_data)
        df.to_excel(save_path, index=False)

    def auto_to_json(self, raw_text):
        raw_text = raw_text.strip()
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

        if '=' in raw_text and '&' in raw_text:
            try:
                return self.url_to_json(raw_text)
            except Exception:
                pass

        raise ValueError("无法识别输入格式")
