import hashlib
from enum import IntEnum, StrEnum
from uuid import UUID


__version__ = "1.0.0"


#   Default values when the service expects a project, an account or a user
DEFAULT_PROJECT = UUID("00000000-0000-0000-0000-000000000000")
DEFAULT_ACCOUNT = UUID("00000000-0000-0000-0000-000000000000")
DEFAULT_USER = UUID("00000000-0000-0000-0000-000000000000")



class Method(IntEnum):
    GET = 1
    POST = 2
    PUT = 3
    PATCH = 4
    DELETE = 5



class HeaderAlias(StrEnum):
    PROJECT_ID = "Project-ID"
    ACCOUNT_ID = "Account-ID"
    AUTHORIZATION = "Authorization"



class Timeout(IntEnum):
    FAST = 3
    MEDIUM = 10
    LONG = 60
    DEFAULT = 30



class Handle(StrEnum):
    PROFILE = "profile/{profile_id}"
    PROFILES = "profiles"
    APPLICATION = "application"


    def resolve(self, **kwargs):
        return self.value.format(**kwargs)



def make_serialize_exception(method, schema, exception, data):
    print(f"Serialization error in method {method}, schema {schema}.\n"
          f"Exception type: {type(exception).__name__}\nMessage: {str(exception)}\n"
          f"Object: {data}")



#   Concatenation and compression of a unique object or link code
def generate_object_code(*args):
    code_string = ''
    for _id in args:
        code_string += str(_id) + ":"
    code_string = code_string.rstrip(":")
    link_code_string_as_bytes = str.encode(code_string)
    hsh = hashlib.sha1() # noqa: S324
    hsh.update(link_code_string_as_bytes)
    compressed_link_code = hsh.hexdigest()
    return compressed_link_code



#   Set a bit flag
def set_flag(flags: int, bit_pos: int) -> int:
    return flags | (1 << bit_pos)


#   Clear a bit flag
def clear_flag(flags: int, bit_pos: int) -> int:
    return flags & ~(1 << bit_pos)


#   Check a bit flag
def test_flag(flags: int, bit_pos: int) -> bool:
    return bool(flags & (1 << bit_pos))



#   Check that the value is a UUID
def is_uuid(id_) -> bool:
    try:
        UUID(id_)
        return True
    except ValueError:
        return False



#   Finds an array of common keys for two dictionaries
def find_common_keys(dict1, dict2):
    common_keys = set(dict1.keys()) & set(dict2.keys())
    return list(common_keys)



#   Check that the class contains the specified attribute
def check_attribute(obj, attr_name):
    return 1 if attr_name in obj.__members__.values() else 0



# Universal function for extracting an attribute from a structure
#    Extracts an object attribute, first checking for the key in a dictionary,
#    then using getattr() for class objects.
def extract_attribute(obj, attr_name):
    # Check whether the object is a dictionary and contains the required key
    if isinstance(obj, dict) and obj.get(attr_name):
        return obj[attr_name]


    # If the object is not a dictionary, try to get the attribute using getattr()
    try:
        return getattr(obj, attr_name)
    except AttributeError:
        return None


#   Returns the default account value if none is passed externally
def get_account(account_id):
    _account_id = _check_uuid(account_id)
    return _account_id if _account_id is not None else DEFAULT_ACCOUNT


#   Returns the default user value if none is passed externally
def get_user(user_id):
    _user_id = _check_uuid(user_id)
    return _user_id if _user_id is not None else DEFAULT_USER


#   Returns the default project value if none is passed externally
def get_project(project_id):
    _project_id = _check_uuid(project_id)
    return _project_id if _project_id is not None else DEFAULT_PROJECT



def _check_uuid(param):
    # If the variable contains a string, convert it to UUID
    if isinstance(param, str):
        return UUID(param)


    # If the variable already contains a UUID object, return it
    if isinstance(param, UUID):
        return param


    return param
