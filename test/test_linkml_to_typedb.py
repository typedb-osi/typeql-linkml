import unittest
import json
from notebooks.schema_utils import build_roles_dict, build_entities_dict, build_types_dict, add_slots_to_dict
from linkml_runtime.utils.schemaview import SchemaView

class Testing(unittest.TestCase):

    def setUp(self):
        yaml_file = "test/test_files/biolink_test.yaml"
        self.view = SchemaView(yaml_file)

    def test_that_roles_dict_matches_linkml(self):
        entities_dict = {}

        actual_roles_dict, _ = build_roles_dict(self.view, entities_dict)

        with open('test/test_files/expected_role_dict.json') as input:
            expected_roles_dict = json.load(input)

        self.assertDictEqual(expected_roles_dict, actual_roles_dict)

    def test_that_pure_entities_dict_matches_linkml(self):

        actual_entities_dict = build_entities_dict(self.view)

        with open('test/test_files/expected_entity_dict.json') as input:
            expected_entities_dict = json.load(input)

        self.assertDictEqual(expected_entities_dict, actual_entities_dict)

    def test_that_roles_are_added_to_entities_as_expected(self):
        
        with open('test/test_files/expected_entity_dict.json') as input:
            pure_entities_dict = json.load(input)

        with open('test/test_files/expected_entity_dict_with_roles.json') as input:
            expected_entities_with_roles_dict = json.load(input)
            
        _, actual_entities_with_roles_dict = build_roles_dict(self.view, pure_entities_dict)

        self.assertDictEqual(expected_entities_with_roles_dict, actual_entities_with_roles_dict)   

    def test_that_types_are_converted_to_typedb(self):

        # typedb only has following types: https://docs.vaticle.com/docs/schema/overview
        # long, double, string, boolean, datetime
        typedb_types = ['long', 'double', 'string', 'boolean', 'datetime']

        # dictionary to map biolink types to typedb types
        type_mapper = {"int":"double", "date":"datetime", "float":"long", "XSDDate":"datetime", "str":"string"}
        
        with open('test/test_files/expected_types.json') as input:
            expected_types = json.load(input)
            
        actual_types = build_types_dict(self.view, typedb_types, type_mapper)

        self.assertDictEqual(expected_types, actual_types)   

    def test_that_slots_are_added_to_converted_to_typedb(self):
        
        # typedb only has following types: https://docs.vaticle.com/docs/schema/overview
        # long, double, string, boolean, datetime
        typedb_types = ['long', 'double', 'string', 'boolean', 'datetime']

        # dictionary to map biolink types to typedb types
        type_mapper = {"int":"double", "date":"datetime", "float":"long", "XSDDate":"datetime", "str":"string"}
        
        with open('test/test_files/expected_types.json') as input:
            bl_special_types = json.load(input)

        with open('test/test_files/expected_types_with_slots.json') as input:
            expected_types = json.load(input)
            
        actual_types =  add_slots_to_dict(bl_special_types, self.view, typedb_types, type_mapper)

        self.assertDictEqual(expected_types, actual_types)   

if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()