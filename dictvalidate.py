class Field(dict):
    pass


class DictValidator:
    def __init__(self, schema):
        self.schema = schema


    def _get_by_fqn(self, fqn, document=None):
        if document is None:
            document = self.schema

        if isinstance(fqn, str):
            fqn = fqn.split('.')

        cur = document
        for name in fqn:
            cur = cur.get(name)
            if cur is None: return None

        return cur


    def _get_schema_type(self, fqn, field=None):
        if field is None:
            field = self._get_by_fqn(fqn)
        if isinstance(field, Field):
            return field.get('type')
        else:
            return field


    def validate(self, document):
        assert isinstance(document, dict)
        
        self.missing = []
        self.extra = []
        self.invalid = []
        
        def check_missing(fqn):
            if self._get_by_fqn(fqn, document) is None:
                self.missing.append(".".join(fqn))
                return True
            return False


        def check_extra(fqn):
            if self._get_by_fqn(fqn) is None:
                self.extra.append(".".join(fqn))
                return True
            return False


        def check_type(fqn, value, expected_type):
            if not isinstance(value, expected_type):
                self.invalid.append({
                    "fqn": ".".join(fqn),
                    "value": value,
                    "error": "type",
                    "message": "Found %s, expected %s." % (type(value).__name__, expected_type.__name__)
                })

        
        def validate(fqn, value):
            data = self._get_by_fqn(fqn)
            type_ = self._get_schema_type(fqn, data)

            check_type(fqn, value, type_)
            if type_ is None:
                return

            if not isinstance(data, Field):
                return

            if data.get('null') is False and value is None:
                self.invalid.append({
                    "fqn": ".".join(fqn),
                    "value": value,
                    "error": "null",
                    "message": "Value cannot be null."
                })
                return

            if type_ is str:
                validate_string(fqn, value, data)


        def validate_string(fqn, value, data):
            if data.get('min_length') and len(value) < data['min_length']:
                self.invalid.append({
                    "fqn": ".".join(fqn),
                    "value": value,
                    "error": "min_length",
                    "message": "Length lower than minimum (%s)." % data['min_length']
                })

            if data.get('max_length') and len(value) > data['max_length']:
                self.invalid.append({
                    "fqn": ".".join(fqn),
                    "value": value,
                    "error": "max_length",
                    "message": "Length higher than maximum (%s)." % data['max_length']
                })
            
            if data.get('empty') is False and len(data) > 0:
                self.invalid.append({
                    "fqn": ".".join(fqn),
                    "value": value,
                    "error": "empty",
                    "message": "Value cannot be empty."
                })

            

        def check_document(document, fqn=[]):
            for name, value in document.items():
                fqn += [name]
                if isinstance(value, dict):
                    check_document(value, fqn)
                elif not check_extra(fqn):
                    validate(fqn, value)
                fqn.pop()


        def check_schema(schema, fqn=[]):
            for name, value in schema.items():
                fqn += [name]
                if isinstance(value, Field):
                    pass # A special dict, needs a good skipping
                elif isinstance(value, dict):
                    check_schema(value, fqn)
                else:
                    check_missing(fqn)
                fqn.pop()

        
        check_document(document)
        check_schema(self.schema)

        return (self.invalid, self.missing, self.extra)


def validate(schema, document):
    DictValidator(schema).validate(document)


def test():
    example = {
        "first": {
            "second": [
                "1", "2", "3"
            ],
            "third": "third answer",
            "fourth": True,
            "fifth": {
                "sixth": 12
            },
            "extra": "haha"
        }
    }
    
    example_validation_schema = {
        "first": {
            "second": str,
            "third": Field(type=str, min_length=2, max_length=10),
            "fourth": bool,
            "fifth": {
                "sixth": Field(type=int)
            },
            "missing": object
        }
    }
    
    x = DictValidator(example_validation_schema)
    result = x.validate(example)
    return (x, result)


if __name__ == "__main__":
    print(test())

