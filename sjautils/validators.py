from functools import reduce
import pytz
from sjautils import utils
from sjautils.date_time import timestamp
import validators

enums = dict(
    NOTIFICATION_DELIVERY_TYPES=['email', 'push', 'inbox'],
    USER_STATUSES=('added', 'invited', 'active', 'disabled', 'EXTERNAL_PROVIDER'),
    USER_TYPES=('user', 'admin', 'cs'),
    PARAM_STATUS={'disabled', 'active'},
    INVITATION_STATUS=('active', 'expired', 'accepted'),  # TODO check these
)


class ValidationException(Exception):
    '''
    Exception on validation issue. Some such Exceptions should have their msg body translated, but not all.
    '''

    def __init__(self, message, i18n_instance=None, desired_lang='en', **msg_parameters):
        '''
        Constructor allows for case of message needing no translation that was not already done in calling context
        and for case of translation being asked for in building message. It is expected that if the message takes
        parameters then these are in %{param_key}s form unless the parameters have already been applied (no translation form only).
        :param message: The message text, perhaps already translated or not needing translation
        :param i18n_instance: if translations is needed then pass the i18n instance and set the desired_lang to desired language.
          This provides the context for doing the translation.
        :param desired_lang: desired language if translation needed, defaults to english
        :param message_parameters: parameter dictionary.
        '''
        if i18n_instance:
            message = i18n_instance.localized_message(message, desired_locales=[desired_lang], **msg_parameters)
        elif msg_parameters:
            message = message.format(**msg_parameters)
        super().__init__(message)


class MissingRequiredException(ValidationException):
    def __init__(self, missing):
        super().__init__('missing required values: %s' % ', '.join(missing))


class UniquenessException(ValidationException):
    def __init__(self, field, value):
        super().__init__('Field %s has non-unique value %s' % (field, value))


class ParamSpec:
    '''
    Superclass of all classes specifying name, type and other legal value checks for parameters/fields.
    '''

    class SimplyInvalid(Exception):
        def __init__(self, var_name, msg):
            super().__init__('%s: %s' % (var_name, msg))

    class RequiredException(ValidationException):
        def __init__(self, spec):
            super().__init__('field %s is required' % spec.name)

    class TypeException(ValidationException):
        def __init__(self, spec, val):
            super().__init__('field %s must be of type %s not %s' % (spec.name, str(spec.param_type), type(val)))

    class SpecificTypeException(ValidationException):
        def __init__(self, spec, fn_name, val):
            super().__init__('could not validate field %s(%s) of type %s' % (fn_name, val, str(spec.param_type)))

    class EnumException(ValidationException):
        def __init__(self, spec, val):
            super().__init__('enum field %s must be one of %s not %s' % (spec.name, str(spec.legal_values), val))

    def __init__(self, name, param_type, description, optional=True, default_val=None, default_fn=None,
                 special_fill_fn=None, external_update_fn=None, required=False):
        '''
        Used for defining and checking types and values for different types of parameters or fields, usually but not
        exclusively for mutator checks.
        :param name: name of field
        :param param_type: the base type that should be satisfied
        :param description: optional description of the field
        :param optional: whether a value for this parameter is optional.
        :param default_val: literal default value to use if parameter is missing and required
        :param default_fn:  a function to calculate default value if missing and required. This function should be niladic. 
        :param special_fill_fn: a few dict based fields have special criteria for filling in missing data, e.g., some
          of the image fields.  This kind of function takes the dictionary supplied as parameter.
        :param external_update_fn: a few parameters are mirrored in external tables.  This function takes the
          key of the instance and the value of the field in the insert or update as parameter.
        '''
        # super().__init__(
        #   name=name, param_type=param_type,
        #   description=description,
        #   optional=optional,
        #   default_fn=default_fn,
        #   default_val=default_val,
        #   special_fill_fn=special_fill_fn,
        #   external_update_fn=external_update_fn
        # )
        if required:  # alternate spec style
            optional = False
        self.name = name
        self.param_type = param_type
        self.description = description
        self.optional = optional
        self.default_val = default_val
        self.default_fn = default_fn
        self.special_fill_fn = special_fill_fn
        self.external_update_fn = external_update_fn

    @property
    def has_default(self):
        return self.default_fn or (self.default_val is not None)

    def default(self):
        '''
        Prefer default_val if present else result of niladic default_fn if present
        :return: default value or None if no means of getting one exist
        '''
        if self.default_val is not None:
            return self.default_val
        elif self.default_fn is not None:
            return self.default_fn()

    def none_check(self, val):
        return self.optional and (val is None)

    def exists(self, val):
        return val is not None

    def check_existence(self, val):
        '''
        checks for missing required parameter value
        :param val: the value found (None if not found)
        :return: True if ok else raises RequiredException
        '''
        if not (self.optional or self.exists(val)):
            raise self.RequiredException(self)
        return True

    def check_type(self, val):
        '''
        Checks the value is of specified type for the parameter spec
        :param val: the value
        :return: True if of correctType otherwise raises TypeException
        '''
        if not isinstance(val, self.param_type):
            raise self.TypeException(self, val)
        return True

    def check_basic_validity(self, val):
        '''
        Checks for existences and type validity. Note type_validity is only checked value exists.
        :param val: value to check
        :return: True is val exists and type is ok or val is None and spec says it is  optional.
          Otherwise throws either RequiredException or TypeException.
        '''
        if self.none_check(val):
            return True
        if self.check_existence(val):
            return self.check_type(val)


class Derived(ParamSpec):
    '''
    Specification for a parameter that is derived rom other data.  Currently this is only used to automatically fill
    in derived values from an overall schema.  
    '''

    def __init__(self, name, param_type, description, fields, fn, **kwargs):
        '''
        
        :param name:  See super
        :param param_type: See super
        :param description: See super
        :param fields: list of names of fields in the data to be used by the deriving function for this field
        :param fn: the deriving function which takes a dictionary of key_value pairs
        :param kwargs: other optional fields of super to avoid endless repeating
        '''
        super().__init__(name, param_type, description, **kwargs)
        self._fields = fields
        self._fn = fn

    def create_value(self, from_data):
        '''
        Derive the value from the supplied data dictiorary
        :param from_data: the data dictionary
        :return: the derived value or None if the needed fields were not in the data.
        '''
        if self.name not in from_data:
            if all([(f in from_data) for f in self._fields]):
                return self._fn(from_data)


class Concatenated(Derived):
    '''
    Used for some of the double keys unfortunately needed by dynamodb GSI at times
    '''

    def __init__(self, name, description, fields, **kwargs):
        '''

        :param name: See super
        :param description: see Super
        :param fields: here these are name of fields to concatenate from supplied data
        :param kwargs: See super
        '''
        joined = lambda d: '|'.join([str(d.get(f)) for f in fields])

        super().__init__(name, str, description, fields, joined, **kwargs)


class Boolean(ParamSpec):
    '''
    Boolean spec
    '''

    def __init__(self, name, description, **kwargs):
        super().__init__(name, bool, description, **kwargs)


class String(ParamSpec):
    '''
    Superclass of String type fields.
    '''

    def __init__(self, name, description, empty_allowed=True, validation_fn=None, unique=False, **kwargs):
        '''

        :param name: See super
        :param description: See super
        :param empty_allowed: whether empty string is allowed
        :param validation_fn: An additional optional function for validation of value. Takes one param - a value to
           check. The function should return True if there was no problem or raise if there was a problem.
        :param unique: whether uniqueness is required, typically only for Persistent table/collection checks
        :param kwargs: See super
        '''
        super().__init__(name, str, description, **kwargs)
        self.empty_allowed = empty_allowed
        self._validation_fn = validation_fn
        self.unique = unique

    def exists(self, val):
        return super().exists(val) if self.empty_allowed else bool(val)

    # TOOD (sja) fix up the unique_in checks
    def check_type(self, val):
        '''
        First do supers type check. If it fails throw TypeException.
        Then if there is a validation_fn run it.  If it throws an exception then
        raise SpecificTypeException.
        :param val: the value to check
        :return:
        '''
        if super().check_type(val):
            if self._validation_fn:
                try:
                    return self._validation_fn(val)
                except Exception as e:
                    raise self.SpecificTypeException(self, self._validation_fn.__name__, val)
        return True


class URL(String):
    '''
    Spec for URL type using validators module
    '''

    def __init__(self, name, description, empty_allowed=False, validation_fn=validators.url, **kwargs):
        super().__init__(name, description, empty_allowed=empty_allowed, validation_fn=validation_fn, **kwargs)


class Domain(String):
    pass


class Email(String):
    '''
    Spec for email type using validators module
    '''

    def __init__(self, name, description, empty_allowed=False, validation_fn=validators.email, **kwargs):
        super().__init__(name, description, empty_allowed=empty_allowed, validation_fn=validation_fn, **kwargs)


class EnumString(String):
    '''
    Spec for Enum type that ensures value is one of the allowed string values.
    '''

    def __init__(self, name, description, legal_values, empty_allowed=False, **kwargs):
        super().__init__(name, description, empty_allowed=empty_allowed, **kwargs)
        self.legal_values = legal_values

    def check_type(self, val):
        if not super().check_type(val):
            raise self.TypeException(self, val)
        if val not in self.legal_values:
            raise self.EnumException(self, val)
        return True


class Timezone(EnumString):
    def __init__(self, name, description, **kwargs):
        super().__init__(name, description, legal_values=pytz.all_timezones, **kwargs)


class Int(ParamSpec):
    def __init__(self, name, description, **kwargs):
        super().__init__(name, int, description, **kwargs)


class Timestamp(Int):
    '''
    Spec for timestamp as int. Sets the default_fn to generate current timestamp.
    '''

    def __init__(self, name, description, **kwargs):
        if 'default_fn' not in kwargs:
            kwargs['default_fn'] = timestamp
        super().__init__(name, description, **kwargs)


class Float(ParamSpec):
    def __init__(self, name, description, **kwargs):
        super().__init__(name, float, description, **kwargs)


class ID(String):
    '''
    Specification for an ID valued field.  Never allowed to be empty.
    '''

    def __init__(self, name, description, **kwargs):
        super().__init__(name, description, empty_allowed=False, **kwargs)


class Dict(ParamSpec):
    '''
    Specification for a field that is dictionary valued with optionsal
    specification for some or all of its keys and expected values.

    Note: another possibility would be to use a Schema to express restrictions on
    dictionary keys and values.  But that looked a bit more finicky.
    '''

    def __init__(self, name, description, subSchema=None, **kwargs):
        '''

        :param name: See super
        :param description: See super
        :param optional: See super
        :param specs: optional param specs for restrictions on the dict used as value for the field
        '''
        super().__init__(name, dict, description, **kwargs)
        self.subSchema = subSchema

    def exists(self, val):
        '''
        Check the existence of everything is the optional specifications for dict keys and values.
        :param val: dict to check
        :return: Return whether all exists or are optional and do not exist in the val
        '''
        exists_at_all = super().exists(val)
        if self.subSchema:
            return reduce(lambda a, b: a and b.exists(val.get(b.name)), self.subSchema.required(), exists_at_all)
        return exists_at_all

    def check_basic_validity(self, val):
        '''
        Checks for existences and type validity. Note type_validity is only checked value exists.
        :param val: value to check
        :return: True is val exists and type is ok or val is None and spec says it is  optional.
          Otherwise throws either RequiredException or TypeException.
        '''
        if self.none_check(val):
            return True
        if self.subSchema and super().exists(val):
            self.subSchema.auto_fill_required({}, val)
            val.update(self.subSchema.auto_fill_optional(val))
            self.subSchema.do_special_fills(val)
            return self.subSchema.validate_insert(val)

        return super().check_basic_validity(val)


class NamedDict(ParamSpec):
    '''
    There are some recursive definitions.  All of these are objects, that
    is they are a dict fields type specification.
    '''

    def __init__(self, name, description, reference, dict_map, fld_map=None, **kwargs):
        '''
        specification in terms of name of what is referenced and some mapping of definitions
        :param name: name of the field
        :param description: description of the field
        :param reference: other dictionary type parameter type name
        :param dict_map: map of type names to dictionary types which may itself
          have recursive elements
        :param id_func: function that returns a uniquer_id for the refeneced item so
          we can short circuit recursive loops when checking validity
        :param kwargs: other general ParamSpec information such as whether required
        '''
        self._reference = reference
        self._mapping = dict_map
        self._fld_map = fld_map
        super().__init__(name, dict, description, **kwargs)

    def get_ref(self):
        return self._mapping[self._reference]

    def exists(self, val):
        '''
        Check the existence of everything is the optional specifications for dict keys and values.
        :param val: dict to check
        :return: Return whether all exists or are optional and do not exist in the val
        '''
        exists_at_all = super().exists(val)
        referenced = self.get_ref()
        if referneced.subSchema:
            return reduce(lambda a, b: a and b.exists(val.get(b.name)), referenced.subSchema.required(), exists_at_all)
        return exists_at_all


class List(ParamSpec):
    '''
    Specification for a list valued field with optional specification that each element must satisfy.
    '''

    def __init__(self, name, description, empty_allowed=True, element_spec=None, **kwargs):
        '''

        :param name: See super
        :param description: See super
        :param optional: See Super
        :param empty_allowed: whether empty list is allowed
        :param element_spec: optional ParamSpec that each element must satisfy
        '''
        super().__init__(name, list, description, **kwargs)
        self.element_spec = element_spec
        self.empty_allowed = empty_allowed

    def exists(self, val):
        return super().exists(val) if self.empty_allowed else bool(val)

    def check_type(self, val):
        '''
        Checks val is a list and if element spec is present checks that each element satisfies
        that specification.
        :param val: value to check
        :return: True or appropriate ParamSpec exception for either the list itself or its elements
          if element specifiaction is present.
        '''
        ok = super().check_type(val)
        if self.element_spec:
            ok = ok and all([self.element_spec.check_type(x) for x in val])
        if not ok:
            raise self.TypeException(self, val)
        return ok


class Schema:
    '''
    A Schema is a collection of ParamSpecs. The class includes methods for checking data against the
    specs and for validating and possibly filling insert and delete data.  The insert checking ensures
    all specs with optional=False have data.
    '''

    def __init__(self, *field_specs):
        '''

        :param field_specs: ParamSpec instances for all fields that are in the schema that we wish to validate
          Required fields should include optional=False to insure insert validation raise if required fields
          are not present.
        '''
        self._specs = list(field_specs)
        self._field_map = {f.name: f for f in self._specs}

    def required(self, additional_filter=None):
        '''
        Returns the param spec map by field name of required fields. An optional filter can be used to
        drop some of the required fields.
        :param additional_filter: optional function taking a ParamSpec and returning False if it should not
         be included in the returned mapping.  Typically used to weed out derived but mandatory fields.
        :return: the mapping of required fields
        '''
        req = {k: v for k, v in self._field_map.items() if not v.optional}
        if additional_filter:
            req = {k: v for k, v in req.items() if additional_filter(v)}
        return req

    def special_fills(self):
        return {k: v for k, v in self._field_map.items() if v.special_fill_fn}

    def get_field(self, name):
        return self._field_map.get(name)

    def has_everything_expected(self, obj):
        '''
        Checks whether an object, likely from database, has all expected fields.
        :param obj: the object to check
        :return: whether it has all required, optional but defaulted, and derivable fields
        '''
        has_fields = lambda src: all([k in obj for k in src])
        derivable = {k: v for k, v in self.derived().items() if v.create_value(obj)}
        ok = has_fields(self.required())
        ok = ok and has_fields(self.optional_with_defaults())
        return ok and has_fields(derivable)

    def unique(self):
        return {k: v for k, v in self._field_map.items() if getattr(v, 'unique', False)}

    def do_special_fills(self, data, is_insert=True):
        '''
        This is for cases where some values for fields  to be inserted or updated needs to be run through a special
        transforming function
        :param data: the data to examine and possibly modify for such cases
        :return:
        '''
        special_fills = {k: v for k, v in self._field_map.items() if (k in data and v.special_fill_fn)}
        for k, spec in special_fills:
            data[k] = spec.special_fill_fn(data[k])

    def optional_fields(self):
        return {k: v for k, v in self._field_map.items() if v.optional}

    def optional_with_defaults(self):
        return {k: v for k, v in self.optional_fields().items() if v.has_default}

    def derived(self):
        return {k: v for k, v in self._field_map.items() if isinstance(v, Derived)}

    def auto_fill_optional(self, data):
        opt_w_default = {k: v.default for k, v in self._field_map.items() if v.optional and (v.has_default)}
        return {k: v() for k, v in opt_w_default.items() if k not in data}

    def auto_fill_derived(self, data, update_target=None):
        # treated derived fields as special in that we always want to include if prerequites fulfillemd
        target = update_target or {}
        target.update(data)
        present = lambda k: k in target
        for k, v in self.derived().items():
            if present(k):
                continue
            val = v.create_value(target)
            if val is not None:
                data[k] = val

    def auto_fill_required(self, key, data):
        '''
        Auto fill any required fields missing from data that we have default information for.
        :param key: keys of the table or data structure as a dict. These we never autofill
        :param data: the data to use possibly auto fill some field names and values in
        :return: None. updates data for such fields
        '''
        required = self.required()

        missing = {k: v for k, v in required.items() if k not in data}
        for k, spec in missing.items():
            if k in key:
                continue
            default = spec.default()
            if default is not None:
                data[k] = default

    def validate_item(self, data):
        '''
        Like validate_insert except gathers and returns list of exceptions for all invalid
        field specs against the data
        :param data: the item or data dict that to be checked for satisfying the spec
        :return: wherether the spec is satisfied and a possibly list of exception enconuntered
        '''
        required = self.required()

        ok, exceptions = True, []

        def note_exception(e):
            ok = False
            exceptions.append(e)

        missing = [r for r in required if r not in data]
        if missing:
            ok = False
            note_exception(MissingRequiredException(missing))
        for key in data.keys():
            spec = self._field_map.get(key)
            if spec:
                try:
                    spec.check_basic_validity(data.get(spec.name))
                except Exception as e:
                    note_exception(e)
        return ok, exceptions

    def validate_insert(self, data):
        '''
        After auto_fills validate that we have proper values for all required fields
        :param data: The dict data to validate
        :return: True if everything required is present and valid. Raises MissingRequired if not
          all required fields are present. Otherwise raise the appropriate ParamSpec exception for
          some invalid value encountered.
        '''
        required = self.required()

        missing = [r for r in required if r not in data]
        if missing:
            raise MissingRequiredException(missing)
        for key in data.keys():
            spec = self._field_map.get(key)
            if spec:
                spec.check_basic_validity(data.get(spec.name))
        return True

    def check_unique(self, item, data_unique):
        for k, v in data_unique.items():
            if item.get(k) == v:
                raise UniquenessException(k, v)

    def ensure_defaults(self, a_schema):
        self._field_map.update(a_schema._field_map)
        self._specs = [v for v in self._field_map.values()]

    def unique_in_items(self, data_unique, items, key=None, check_key=False):
        key = key or {}
        check_key = check_key and key
        same_key = lambda item: all([item[k] == key[k] for k in key.keys()])
        for item in items:
            self.check_unique(item, data_unique)

    def validate_update_data(self, data):
        '''
        Validates the value for each key in data by its corresponding PramaSpec, if any.
        :param data: the data to evaluate
        :return: True if all values are valid otherwise raises the appropriate ParamSpec exception
          for the first bad value encountered.
        '''
        for k, v in data.items():
            spec = self._field_map.get(k)
            if spec:
                spec.check_basic_validity(v)
        return True


class StandardDBSchema(Schema):
    defaults = Schema(
        ID('id', 'generated unique id', optional=False, default_fn=utils.generate_unique_id),
        Timestamp('created_at', 'when instance was created', optional=False),
        Timestamp('updated_at', 'when instance was created', optional=False))

    def __init__(self, *field_specs):
        super().__init__(*field_specs)
        self.ensure_defaults(self.__class__.defaults)
