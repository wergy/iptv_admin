from mongoengine import EmbeddedDocument, StringField, IntField, ListField, EmbeddedDocumentField, FloatField

import app.constants as constants


# {"urls": [{"id": 81,"uri": "tcp://localhost:1935"}]}
class Url(EmbeddedDocument):
    _next_url_id = 0

    id = IntField(default=lambda: Url.generate_id(), required=True)
    uri = StringField(default='test', max_length=constants.MAX_URL_LENGTH, required=True)

    @staticmethod
    def generate_id():
        current_value = Url._next_url_id
        Url._next_url_id += 1
        return current_value


class Urls(EmbeddedDocument):
    urls = ListField(EmbeddedDocumentField(Url))


class Logo(EmbeddedDocument):
    path = StringField(default=constants.INVALID_LOGO_PATH, required=True)
    x = IntField(default=constants.DEFAULT_LOGO_X, required=True)
    y = IntField(default=constants.DEFAULT_LOGO_Y, required=True)
    alpha = FloatField(default=constants.DEFAULT_LOGO_ALPHA, required=True)

    def is_valid(self):
        return self.path != constants.INVALID_LOGO_PATH

    def to_dict(self) -> dict:
        return {'path': self.path, 'position': '{0},{1}'.format(self.x, self.y), 'alpha': self.alpha}


class Size(EmbeddedDocument):
    width = IntField(default=constants.INVALID_WIDTH, required=True)
    height = IntField(default=constants.INVALID_HEIGHT, required=True)

    def is_valid(self):
        return self.width != constants.INVALID_WIDTH and self.height != constants.INVALID_HEIGHT

    def __str__(self):
        return '{0}x{1}'.format(self.width, self.height)


class Rational(EmbeddedDocument):
    num = IntField(default=constants.INVALID_RATIO_NUM, required=True)
    den = IntField(default=constants.INVALID_RATIO_DEN, required=True)

    def is_valid(self):
        return self.num != constants.INVALID_RATIO_NUM and self.den != constants.INVALID_RATIO_DEN

    def __str__(self):
        return '{0}:{1}'.format(self.num, self.den)
