class Maker:
    @classmethod
    def make_entry(cls, json: dict):
        cl = cls()
        cl.update_entry(json)
        return cl

    def update_entry(self, json: dict):
        if json is None:
            raise ValueError('Invalid input')

    @staticmethod
    def check_required_type(field: str, expected, json: dict):
        if json is None:
            raise ValueError('Invalid input')

        value_field = json.get(field, None)
        if value_field is None:
            raise ValueError('Invalid input({0} required)'.format(field))

        actual = type(value_field)
        if not Maker._check_is_same_types(actual, expected):
            raise ValueError('Invalid input field({0}) actual type: {1}, expected: {2}'.format(field, actual, expected))

        return True, value_field

    @staticmethod
    def check_optional_type(field: str, expected, json: dict):
        if json is None:
            raise ValueError('Invalid input')

        value_field = json.get(field, None)
        if value_field is not None:  # optional field
            actual = type(value_field)
            if not Maker._check_is_same_types(actual, expected):
                raise ValueError(
                    'Invalid input field({0}) actual type: {1}, expected: {2}'.format(field, actual, expected))

            return True, value_field

        return False, None

    @staticmethod
    def _check_is_same_types(actual, expected) -> bool:
        if actual is expected:
            return True

        if (int == actual or int == expected) and (float == actual or float == expected):
            return True

        return False

