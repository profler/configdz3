import unittest
from parser import ConfigParser 

class TestConfigParser(unittest.TestCase):

    def test_parse_constant(self):
        parser = ConfigParser()
        lines = ["const max_connections = 100"]
        parser.parse(lines)
        self.assertEqual(parser.constants["max_connections"], 100)

    def test_parse_single_structure(self):
        parser = ConfigParser()
        lines = [
            "struct {",
            "    name = \"server01\",",
            "    ip = \"192.168.1.1\",",
            "    port = 8080",
            "}"
        ]
        parser.parse(lines)
        self.assertEqual(len(parser.structures), 1)
        expected = {
            "name": "server01",
            "ip": "192.168.1.1",
            "port": 8080
        }
        self.assertEqual(parser.structures[0], expected)

    def test_parse_with_constant_reference(self):
        parser = ConfigParser()
        lines = [
            "const host_name = \"server01\"",
            "struct {",
            "    name = $[host_name],",
            "    ip = \"192.168.1.1\"",
            "}"
        ]
        parser.parse(lines)
        self.assertEqual(len(parser.structures), 1)
        expected = {
            "name": "server01",
            "ip": "192.168.1.1"
        }
        self.assertEqual(parser.structures[0], expected)

    def test_to_xml(self):
        parser = ConfigParser()
        lines = [
            "struct {",
            "    name = \"example\",",
            "    value = 123",
            "}"
        ]
        parser.parse(lines)
        xml_output = parser.to_xml()
        expected_xml = """<?xml version="1.0" ?>
<configuration>
    <struct>
        <name>example</name>
        <value>123</value>
    </struct>
</configuration>
"""
        self.assertEqual(xml_output.strip(), expected_xml.strip())

    def test_syntax_error_on_missing_brace(self):
        parser = ConfigParser()
        lines = [
            "struct {",
            "    key = value"
        ] 
        with self.assertRaises(SyntaxError):
            parser.parse(lines)

    def test_syntax_error_on_invalid_constant(self):
        parser = ConfigParser()
        lines = ["const 123_invalid = value"]
        with self.assertRaises(SyntaxError):
            parser.parse(lines)

    def test_unknown_constant_reference(self):
        parser = ConfigParser()
        lines = [
            "struct {",
            "    key = $[undefined_constant]",
            "}"
        ]
        with self.assertRaises(ValueError):
            parser.parse(lines)

if __name__ == "__main__":
    unittest.main()