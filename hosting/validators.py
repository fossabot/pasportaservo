from string import digits
from datetime import date
import re

from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from .utils import split, title_with_particule


def validate_not_all_caps(value):
    """Tries to figure out whether value is all caps and shouldn't.
    Validates until 3 characters and non latin strings.
    """
    if len(value) > 3 and value[-1:].isupper() and value == value.upper():
        message = _("Today is not CapsLock day. Please try with '%(correct_value)s'.")
        raise ValidationError(message % {'correct_value': title_with_particule(value)}, code='caps')


def validate_not_too_many_caps(value):
    """Tries to figure out whether value has too much caps.
    Maximum two capital per word.
    """
    authorized_begining = ("a", "de", "la", "mac", "mc")
    message = _("It seems there are too many uppercase letters. Try with '%(correct_value)s'.")
    message = message % {'correct_value': title_with_particule(value)}

    words = split(value)
    nb_word = len(words)
    if not any(words):
        pass  # For non latin letters
    elif value == value.upper():
        validate_not_all_caps(value)
    else:
        for word in words:
            nb_caps = sum(1 for char in word if char.isupper())
            if nb_caps > 1:
                if any([word.lower().startswith(s) for s in authorized_begining]):
                    # This should validate 'McCoy'
                    if nb_caps > 2:
                        raise ValidationError(message, code='caps')
                else:
                    raise ValidationError(message, code='caps')


def validate_no_digit(value):
    """Validates if there is not digit in the string."""
    message = _("Digits are not allowed.")
    if any([char in digits for char in value]):
        raise ValidationError(message, code='digits')


def validate_latin(value):
    """Validates if the string starts with latin characters."""
    message = _("Please provide this data in Latin characters, preferably in Esperanto. "
                "The source language can be possibly stated in parentheses.")
    if not re.match(r'^[\u0041-\u005A\u0061-\u007A\u00C0-\u02AF\u0300-\u036F\u1E00-\u1EFF]', value):
        # http://kourge.net/projects/regexp-unicode-block
        raise ValidationError(message, code='non-latin')


def validate_not_in_future(datevalue):
    """Validates if the date is no later than today."""
    MaxValueValidator(date.today())(datevalue)


@deconstructible
class TooFarPastValidator(object):
    def __init__(self, number_years):
        self.number_years = number_years

    def __call__(self, datevalue):
        """Validates if the date is not earlier than the specified number of years ago."""
        now = date.today()
        try:
            back_in_time = now.replace(year=now.year - self.number_years)
        except ValueError:
            back_in_time = now.replace(year=now.year - self.number_years, day=now.day-1)
        MinValueValidator(back_in_time)(datevalue)

    def __eq__(self, other):
        return (isinstance(other, TooFarPastValidator) and self.number_years == other.number_years)

    def __ne__(self, other):
        return not (self == other)


@deconstructible
class TooNearPastValidator(TooFarPastValidator):
    def __call__(self, datevalue):
        """Validates if the date is not later than the specified number of years ago."""
        now = date.today()
        try:
            back_in_time = now.replace(year=now.year - self.number_years)
        except ValueError:
            back_in_time = now.replace(year=now.year - self.number_years, day=now.day-1)
        MaxValueValidator(back_in_time)(datevalue)


def validate_image(content):
    """Validate if Content Type is an image."""
    if getattr(content.file, 'content_type', None):
        content_type = content.file.content_type.split('/')[0]
        if content_type != 'image':
            raise ValidationError(_("File type is not supported"), code='file-type')


def validate_size(content):
    """Validate if the size of the content in not too big."""
    MAX_UPLOAD_SIZE = 102400  # 100kB
    if content.file.size > MAX_UPLOAD_SIZE:
        message = _("Please keep filesize under %(limit)s. Current filesize %(current)s") % {
            'limit': filesizeformat(MAX_UPLOAD_SIZE),
            'current': filesizeformat(content.file.size)}
        raise ValidationError(message, code='file-size')
