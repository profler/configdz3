import re
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

class ConfigParser:
    def __init__(self):
        self.constants = {}
        self.structures = []
        self.current_structure = None

    def parse(self, lines):
        buffer = []
        for line in lines:
            line = line.strip()
            if line.startswith('//') or not line:
                continue  # Игнорируем комментарии и пустые строки
            if line.startswith('const'):
                self.parse_constant(line)
            elif line.startswith('struct'):
                if self.current_structure is not None:
                    raise SyntaxError("Вложенные структуры не поддерживаются")
                self.current_structure = []
                buffer.append(line)
            elif line.endswith('}'):
                if self.current_structure is None:
                    raise SyntaxError("Неожиданная закрывающая скобка }")
                buffer.append(line)
                self.parse_structure('\n'.join(buffer))
                buffer = []
                self.current_structure = None
            elif self.current_structure is not None:
                buffer.append(line)
            else:
                raise SyntaxError(f"Неизвестная конструкция: {line}")

    def parse_constant(self, line):
        match = re.match(r'const\s+([_a-z]+)\s*=\s*(.+)', line)
        if not match:
            raise SyntaxError(f"Ошибка синтаксиса в константе: {line}")
        name, value = match.groups()
        self.constants[name] = self.evaluate_value(value)

    def parse_structure(self, content):
        match = re.match(r'struct\s*{(.+?)}', content, re.DOTALL)
        if not match:
            raise SyntaxError(f"Ошибка синтаксиса в структуре: {content}")
        struct_content = match.group(1).strip()
        items = self.parse_items(struct_content)
        self.structures.append(items)

    def parse_items(self, content):
        items = {}
        buffer = []
        depth = 0
        for item in re.split(r',\s*(?![^{]*\})', content):  # Разделяем по запятой, игнорируя запятые внутри фигурных скобок
            item = item.strip()
            if 'struct {' in item:
                depth += 1
            if '}' in item:
                depth -= 1
            buffer.append(item)
            if depth == 0:
                combined_item = ' '.join(buffer).strip()
                if '=' in combined_item:
                    key, value = combined_item.split('=', 1)
                    items[key.strip()] = self.evaluate_value(value.strip())
                buffer = []
        return items

    def evaluate_value(self, value):
        value = value.strip()
        # Проверка на ссылку на константу
        match = re.match(r'\$\[([_a-zA-Z]+)\]', value)
        if match:
            const_name = match.group(1)
            if const_name in self.constants:
                return self.constants[const_name]
            else:
                raise ValueError(f"Неизвестная константа: {const_name}")

        if value.isdigit():
            return int(value)
        elif re.match(r'"[^"]*"', value):  # Проверка на строку
            return value.strip('"')  # Убираем кавычки
        elif value.lower() in ['true', 'false']:  # Обработка логических значений
            return value.lower() == 'true'
        elif re.match(r'struct\s*{(.+?)}', value, re.DOTALL):  # Проверка на вложенную структуру
            match = re.match(r'struct\s*{(.+?)}', value, re.DOTALL)
            if match:
                nested_content = match.group(1).strip()
                return self.parse_items(nested_content)
        else:
            raise ValueError(f"Неизвестное значение: {value}")
    
    def to_xml(self):
        root = ET.Element("configuration")
        for struct in self.structures:
            self.add_struct_to_xml(root, struct)
        # Форматируем XML с отступами
        xml_string = ET.tostring(root, encoding='unicode')
        parsed_xml = minidom.parseString(xml_string)
        return parsed_xml.toprettyxml(indent="    ")  # Используем 4 пробела для отступов

    def add_struct_to_xml(self, parent, struct):
        struct_elem = ET.SubElement(parent, "struct")
        for key, value in struct.items():
            if isinstance(value, dict):
                self.add_struct_to_xml(struct_elem, value)
            else:
                item_elem = ET.SubElement(struct_elem, key)
                item_elem.text = str(value)

def main():
    if len(sys.argv) != 2:
        print("Использование: python config_parser.py <путь_к_файлу>")
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        parser = ConfigParser()
        parser.parse(lines)
        xml_output = parser.to_xml()
        print(xml_output)

    except (FileNotFoundError, SyntaxError, ValueError) as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()