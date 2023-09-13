# importing the module  
from re import sub  
from typedb.client import TypeDB, SessionType, TransactionType
# classes are named in CamelCase form
# slots are named in snake_case form
# types are named in snake_case form
# To avoid ambiguity in semantics, prefixes are MUST for classes and certain slots.
# To avoid ambiguity it semantics, prefixes are RECOMMENDED for all slots.

# creating a function which will convert string to camelcase  
def convert_to_camelCase(my_string):  
    my_string = sub(r"(_|-)+", " ", my_string).title().replace(" ", "")  
    return my_string[0].upper() + my_string[1:]  

# creating a function which will convert string to snakecase 
def convert_to_snakeCase(my_string):  
    my_string = sub(r"(_|-)+", " ", my_string).lower().replace(" ", "_")  
    return my_string

def set_nested_value(dictionary, keys, value):
    for key in keys[:-1]:
        dictionary = dictionary.setdefault(key, {})
    dictionary[keys[-1]] = value

def build_tql_define(main, type, value = None, abstract=False):
    value_q = ''
    abstract_q = ''
    if value:
        value_q = f', value {value}'
    if abstract:
        abstract_q =  f', abstract'
    query = f'define {main} sub {type}{abstract_q}{value_q};'
    return query

def build_tql_entity(name, type, attributes):
    if attributes != '':
        attributes = ', ' + attributes
    query = f'define {name} sub {type}{attributes};'
    return query

def build_tql_rel(name, type, attributes, plays="", abstract=False):
    abstract_q = ""
    if abstract:
        abstract_q =  f', abstract'
    if attributes == ', ':
        attributes = ''
    query = f'define {name} sub {type}{abstract_q}{attributes}{plays};'
    return query

def write_query_transaction(query, dbname, localhost="localhost:1729"):
    with TypeDB.core_client(localhost) as client:
        with client.session(dbname, SessionType.SCHEMA) as session:
            with session.transaction(TransactionType.WRITE) as write_transaction:    
                write_transaction.query().define(query)
                write_transaction.commit()


def build_roles_dict(view, entities_dict):
    """
    view: SchemaView object from linkML
    entities_dict: dictionary containing entities 

    Description: Loops through roles extracted from LinkML model and builds a dictionary of TypeDB-friendly queries for each role. 
    Updates entities with relevant associations
    """
    roles_dict = {}

    roles_dict['association'] = {'name' : 'association', 
                        'type': 'relation', 
                        'relates': '',
                        'abstract': True}

    for a in view.class_descendants('association'): 
        
        if a != 'association':
            rel_type = view.get_class(a)['is_a']
            if rel_type != 'association':
                rel_type = convert_to_camelCase(view.get_class(a)['is_a'])

            owns =", " + ", ".join("owns "+convert_to_snakeCase(d) for d in view.get_class(a)['defining_slots'] if d not in view.class_slots('association'))
            if len(owns) < 3:
                owns = ''
            
            roles = view.get_class(a)['slot_usage'].keys()
            parent_class_slots = view.get_class(view.get_class(a)['is_a'])['slot_usage'].keys()            

            roles = [r for r in roles if r not in parent_class_slots]

            roles_dict[a]= {
                'name' : convert_to_camelCase(a),  
                'type': rel_type, 
                'relates': ', ' +  ", ".join("relates "+convert_to_camelCase(r) for r in roles) + owns, 
                'abstract': False
            }
            
            for r in roles: 
            
                slot = view.get_class(a)['slot_usage'][r]
                any_of = list(view.get_class(a)['slot_usage'][r]['any_of']) + [slot]


                for attribute in any_of:
                    division = ''
                    if type(attribute) != str:
                        
                        # Update entity queries dict with association relations
                        range=attribute['range']
                        if range and range in entities_dict.keys():
                            if entities_dict[range]['attributes'] != '':
                                division = ', '
                                
                            entities_dict[range]['attributes'] = f"{entities_dict[range]['attributes']}{division}plays {convert_to_camelCase(a)}:{convert_to_camelCase(r)}"

                        # Builds roles query dict
                        if range and range in roles_dict.keys():
                        
                            if 'plays' in roles_dict[range].keys():
                                roles_dict[range]['plays'] = f"{roles_dict[range]['plays']}, plays {convert_to_camelCase(a)}:{convert_to_camelCase(r)}"
                            else:
                                roles_dict[range]['plays'] = f", plays {convert_to_camelCase(a)}:{convert_to_camelCase(r)}"

    return roles_dict, entities_dict

def build_entities_dict(view):
    """
    view: SchemaView object from linkML

    Description: Loops through entities extracted from LinkML model and builds a dictionary of TypeDB-friendly queries for each entity. 
    """
    entities_dict = {}

    # all descendants of named thing are either entities or attributes
    for c in view.class_descendants('named thing'):
        if view.get_class(c).name != "named thing" or view.get_class(c).name != "attribute":

            subtype = convert_to_camelCase(view.get_class(c)['is_a'])

            if subtype in ['Entity']:
                subtype = 'entity'
            entities_dict[view.get_class(c).name] = {'name':convert_to_camelCase(c), 'type':subtype}

            attributes = view.class_slots(c)
            if (len(attributes) > 0):
                parent_class_slots = view.class_slots(view.get_class(c)['is_a']) + ["has attribute", "type"]
                if c == 'named thing': 
                    parent_class_slots = ['type']
                ## add ' owns ' to each attribute and join all attributes with ','
                attribute_string = ", ".join("owns "+convert_to_snakeCase(a) for a in attributes if (a not in parent_class_slots))
                
                entities_dict[view.get_class(c).name]['attributes'] = attribute_string

    for c in view.all_classes():
        if view.get_class(c)['mixin']==True:

            attributes = view.class_slots(c)

            if (len(attributes) > 0):
                entities_dict[view.get_class(c).name] = {'name':convert_to_camelCase(c), 'type':'entity'}
                attribute_string = ", ".join("owns "+convert_to_snakeCase(a) for a in attributes if (a not in ["has attribute", "type"]))
                
                entities_dict[view.get_class(c).name]['attributes'] = attribute_string
                
    return entities_dict

def build_types_dict(view, typedb_types, type_mapper):

    # typedb only has following types: https://docs.vaticle.com/docs/schema/overview
    # long, double, string, boolean, datetime
    
    types = view.all_types()

    # additional biolink types
    biolink_types = ['ncname', 'decimal', 'uriorcurie', 'curie', 'uri', 'objectidentifier', 'nodeidentifier', 'XSDTime', 'XSDDate', 'time']


    bl_special_types = {
        "uriorcurie": {"type": "attribute", "abstract": True, "value": "string"},
        "curie": {"type": "uriorcurie", "abstract": False},
        "uri": {"type": "uriorcurie", "abstract": False},
        "time": {"type": "attribute", "abstract": True, "value": "datetime"},
        "XSDTime": {"type": "time", "abstract": False, "value": "datetime"},
        "ncname":  {"type": "attribute", "abstract": False, "value": "string"},
    }

    types = view.all_types()
    for t in types:
        if (t not in typedb_types+biolink_types):
            if (view.get_type(t)['base']): # this covers attributes which are of the main types
                bl_special_types[convert_to_snakeCase(t)] = {"type": "attribute", "value": type_mapper[view.get_type(t)['base']], "abstract": False}
            elif (view.get_type(t)['typeof']):  # this covers attributes which of sub types
                if (view.get_type(t)['typeof'] in typedb_types):
                    bl_special_types[convert_to_snakeCase(t)] = {"type": "attribute", "value": view.get_type(t)['typeof'], "abstract": False}
                else:
                    bl_special_types[convert_to_snakeCase(t)] = {"type": view.get_type(t)['typeof'], "abstract": False}
            else:
                print("ERROR: "+t+" cannot be mapped to typedb types: long, double, string, boolean, datetime")

    return bl_special_types

def add_slots_to_dict(bl_special_types, view, typedb_types, type_mapper ,default_atribute_type = "string"):

    default_atribute_type = "string"

    all_slots = view.all_slots()
    
    ## need to fix child attributes using 'is_a'
    for s in all_slots:
        # "type" is a protected word in typedb
        if view.get_slot(s)['name']!="type":
            # if (view.get_slot(s)['range']):
            if (view.get_slot(s)['range'] in typedb_types):
                # if attribute has range and it belongs to typedb_types, then it is fine
                bl_special_types[convert_to_snakeCase(view.get_slot(s)['name'])] = {"type": "attribute", "value": view.get_slot(s)['range'], "abstract": False}
            elif (view.get_slot(s)['range'] in type_mapper.keys()):
                bl_special_types[convert_to_snakeCase(view.get_slot(s)['name'])] = {"type": "attribute", "value": type_mapper[view.get_slot(s)['range']], "abstract": False}
            else:
                # if it is not in typedb_types, then we just give it the default type for the time being
                bl_special_types[convert_to_snakeCase(view.get_slot(s)['name'])] = {"type": "attribute", "value": default_atribute_type, "abstract": False}

    return bl_special_types