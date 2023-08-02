import html
import json
import re

from django import forms
from django.contrib.gis.geos import Point as GeoPoint
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context
from django.test import TestCase, override_settings, tag

from bs4 import BeautifulSoup
from factory import Faker

from hosting.widgets import (
    ClearableWithPreviewImageInput, CustomNullBooleanSelect,
    ExpandedMultipleChoice, InlineRadios,
    MultiNullBooleanSelects, TextWithDatalistInput,
)
from maps.widgets import AdminMapboxGlWidget, MapboxGlWidget

from ..assertions import AdditionalAsserts


@tag('forms', 'widgets')
class ClearableWithPreviewImageInputWidgetTests(TestCase):
    def test_format_value(self):
        widget = ClearableWithPreviewImageInput()
        self.assertIsNone(widget.format_value(None))
        self.assertIsNone(widget.format_value(""))
        self.assertIsNone(widget.format_value("test.jpeg"))

        faker = Faker._get_faker()
        dummy_file = SimpleUploadedFile(
            faker.file_name(category='image'), faker.image(size=(10, 10), image_format='png'))
        self.assertIsNone(widget.format_value(dummy_file))

        # We need to emulate django.db.models.fields.files.FieldFile without
        # actually creating one and its containing model.
        dummy_file.url = f"test_avatars/$/{dummy_file.name}.png"
        # A FieldFile-resembling value with a URL is expected to result in a
        # return value which can be converted to a template fragment.
        result = widget.format_value(dummy_file)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'url'))
        self.assertEqual(result.url, dummy_file.url)
        result_string = str(result)
        self.assertTrue(result_string.startswith('<img '))
        self.assertIn(f'src="{dummy_file.url}"', result_string)
        self.assertIn('name="image-preview"', result_string)

    def test_render(self):
        widget = ClearableWithPreviewImageInput()
        faker = Faker._get_faker()
        dummy_file = SimpleUploadedFile(
            faker.file_name(category='image'), faker.image(size=(10, 10), image_format='gif'))
        dummy_file.url = f"test_uploaded_pictures/$/{dummy_file.name}.gif"
        result = widget.render('picture_field', dummy_file, attrs={'id': 'id_picture_field'})
        result = ' '.join(result.split())  # Remove newlines and excessive whitespace.
        self.assertRegex(result, f'<img [^>]*src="{re.escape(dummy_file.url)}"')
        self.assertRegex(result, '<img [^>]*id="picture_field-preview_id"')


@tag('forms', 'widgets')
class TextWithDatalistInputWidgetTests(TestCase):
    def test_render(self):
        widget = TextWithDatalistInput()
        widget.choices = [(1, "Az"), (2, "By"), (3, "Cx"), (4, "Dw")]
        result = widget.render('code_field', None, attrs={'id': 'id_code_field'})
        result = ' '.join(result.split())  # Remove newlines and excessive whitespace.
        self.assertInHTML(
            '<input id="id_code_field" name="code_field" type="text" list="id_code_field_options">',
            result)
        self.assertRegex(result, '<datalist [^>]*id="id_code_field_options"')


@tag('forms', 'widgets')
class CustomNullBooleanSelectWidgetTests(TestCase):
    NULL_BOOLEAN_CHOICES = [('true', "hij"), ('false', "klm"), ('unknown', "nop")]

    def test_render(self):
        widget = CustomNullBooleanSelect("Pick one", self.NULL_BOOLEAN_CHOICES)

        result = widget.render('null_bool_field', None, attrs={'id': 'id_bool_field'})
        self.assertInHTML(
            '<span id="id_bool_field_label" class="control-label">Pick one</span>',
            result)
        self.assertInHTML(
            '''
            <select id="id_bool_field" name="null_bool_field"
                    aria-labelledby="id_bool_field_label" class="form-control">
                <option value="true">hij</option>
                <option value="false">klm</option>
                <option value="unknown" selected>nop</option>
            </select>
            ''',
            result)

        result = widget.render('null_bool_field', True, attrs={'id': 'id_bool_field'})
        self.assertInHTML('<option value="true" selected>hij</option>', result)
        self.assertInHTML('<option value="unknown">nop</option>', result)

        result = widget.render('null_bool_field', False, attrs={'id': 'id_bool_field'})
        self.assertInHTML('<option value="false" selected>klm</option>', result)
        self.assertInHTML('<option value="unknown">nop</option>', result)

    def test_render_with_prefix(self):
        widget = CustomNullBooleanSelect("Pick another", self.NULL_BOOLEAN_CHOICES, "Here")
        result = widget.render('null_bool_field', "?", attrs={'id': 'id_bool_field'})
        self.assertInHTML(
            '<span id="id_bool_field_label" class="control-label">Here: Pick another</span>',
            result)
        self.assertInHTML('<option value="unknown" selected>nop</option>', result)

    def test_css_class(self):
        widget = CustomNullBooleanSelect("Don't pick", self.NULL_BOOLEAN_CHOICES)

        test_data = [
            ("X", "fancy"),
            ("Y", "not-fancy"),
            ("Z", "first-level form-control required"),
        ]
        for value, css_classes in test_data:
            result = widget.render(
                'null_bool_field', value,
                attrs={'id': 'id_bool_field', 'class': css_classes})
            html = BeautifulSoup(result, 'html.parser')
            select_element = html.find('select')
            with self.subTest(css_class=css_classes, element=select_element):
                self.assertIsNotNone(select_element)
                for css_class in css_classes.split():
                    self.assertIn(css_class, select_element.attrs['class'])
                self.assertEqual(select_element.attrs['class'].count("form-control"), 1)


@tag('forms', 'widgets')
class MultiNullBooleanSelectsWidgetTests(TestCase):
    def test_render_with_numbering(self):
        widget = MultiNullBooleanSelects(
            [("First", "Go"), ("Second", "Stop")],
            [('false', "kP"), ('unknown', "nM"), ('true', "hS")]
        )
        result = widget.render('multi_value_field', [], attrs={'id': 'id_multi_value_field'})
        html = BeautifulSoup(result, 'html.parser')

        with self.subTest(container=' '.join(result.split())):
            with self.subTest(widget_qualifier=0):
                label_element = html.find('span', id='id_multi_value_field_0_label')
                self.assertIsNotNone(label_element)
                self.assertEqual(label_element.string, "Go: First")
                select_element = html.find(
                    'select', id='id_multi_value_field_0', attrs={'name': 'multi_value_field_0'})
                self.assertIsNotNone(select_element)

            with self.subTest(widget_qualifier=1):
                label_element = html.find('span', id='id_multi_value_field_1_label')
                self.assertIsNotNone(label_element)
                self.assertEqual(label_element.string, "Stop: Second")
                select_element = html.find(
                    'select', id='id_multi_value_field_1', attrs={'name': 'multi_value_field_1'})
                self.assertIsNotNone(select_element)

    def test_render_with_naming(self):
        widget = MultiNullBooleanSelects(
            {'go': ("First", None), 'stop': ("Second", None)},
            [('false', "kP"), ('unknown', "nM"), ('true', "hS")]
        )
        result = widget.render('multi_value_field', [], attrs={'id': 'id_multi_value_field'})
        html = BeautifulSoup(result, 'html.parser')

        with self.subTest(container=' '.join(result.split())):
            with self.subTest(widget_qualifier='go'):
                label_element = html.find('span', id='id_multi_value_field_0_label')
                self.assertIsNotNone(label_element)
                self.assertEqual(label_element.string, "First")
                select_element = html.find(
                    'select', id='id_multi_value_field_0', attrs={'name': 'multi_value_field_go'})
                self.assertIsNotNone(select_element)

            with self.subTest(widget_qualifier='stop'):
                label_element = html.find('span', id='id_multi_value_field_1_label')
                self.assertIsNotNone(label_element)
                self.assertEqual(label_element.string, "Second")
                select_element = html.find(
                    'select', id='id_multi_value_field_1', attrs={'name': 'multi_value_field_stop'})
                self.assertIsNotNone(select_element)


@tag('forms', 'widgets')
class InlineRadiosWidgetTests(TestCase):
    def test_render(self):
        class DummyForm(forms.Form):
            the_future = forms.ChoiceField(choices=[(5, "eV"), (6, "fU"), (7, "gT")])

        widget = InlineRadios('the_future')
        result = widget.render(DummyForm(), 'default', Context({}))
        html = BeautifulSoup(result, 'html.parser')
        with self.subTest(container=' '.join(result.split())):
            self.assertNotIn('<div class="radio">', result)
            label_element = html.find('label', attrs={'for': 'id_the_future_1'})
            self.assertIsNotNone(label_element)
            self.assertIn("radio-inline", label_element.attrs['class'])

        widget = InlineRadios('the_future', radio_label_class="mark-me-up")
        result = widget.render(DummyForm(), 'default', Context({}))
        html = BeautifulSoup(result, 'html.parser')
        with self.subTest(container=' '.join(result.split())):
            self.assertNotIn('<div class="radio">', result)
            label_element = html.find('label', attrs={'for': 'id_the_future_2'})
            self.assertIsNotNone(label_element)
            self.assertIn("radio-inline", label_element.attrs['class'])
            self.assertIn("mark-me-up", label_element.attrs['class'])


@tag('forms', 'widgets')
class ExpandedMultipleChoiceWidgetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        class MultiSelects(forms.widgets.MultiWidget):
            def decompress(self, value):
                return value or []

        class MultiChoicesField(forms.MultiValueField):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.widget = MultiSelects([f.widget for f in self.fields])

            def compress(self, data_list):
                return data_list

        class DummyForm(forms.Form):
            the_past = MultiChoicesField(
                [
                    forms.ChoiceField(choices=[
                        (101, "freshman"), (202, "sophomore"), (303, "junior"), (404, "senior"),
                    ]),
                    forms.ChoiceField(choices=[
                        (True, "diploma"), (False, "certificate"),
                    ]),
                ],
            )

        cls.DummyForm = DummyForm

    def test_render(self):
        widget = ExpandedMultipleChoice('the_past')

        form = self.DummyForm()
        result = widget.render(form, 'default', Context({}))
        html = BeautifulSoup(result, 'html.parser')
        # The form elements are expected to be rendered in a container corresponding
        # to the form's multi-value field.
        container_element = html.select('div#id_the_past_form_element')
        self.assertEqual(len(container_element), 1)
        self.assertNotIn("collapse", container_element[0].attrs.get('class', {}))
        self.assertNotIn('aria-expanded', container_element[0].attrs)
        # No control label is expected to be rendered by default.
        self.assertEqual(len(html.select('label.control-label')), 0)
        for i, subfield in enumerate(form.fields['the_past'].fields, start=1):
            element_id = f'id_the_past_option_{i}_form_element'
            with self.subTest(container_id=element_id):
                element = html.find('div', id=element_id, class_="form-group")
                self.assertIsNotNone(element)
                subelement = element.find('div', id=f'id_the_past_{i-1}')
                self.assertIsNotNone(subelement)
                self.assertIn("btn-group", subelement.attrs['class'])
                self.assertIn("btn-group-toggle", subelement.attrs['class'])
                for opt in subfield.choices:
                    optelement = subelement.find(
                        'input',
                        type='radio', attrs={'name': f'the_past_{i-1}', 'value': str(opt[0])})
                    with self.subTest(option=opt, element=optelement):
                        self.assertIsNotNone(optelement)
                        self.assertNotIn('checked', optelement.attrs)
                        # Each radio input field is expected to be wrapped by a label
                        # styled as a button with text corresponding to the option.
                        self.assertEqual(optelement.parent.name, 'label')
                        self.assertEqual(
                            optelement.attrs.get('id'), optelement.parent.attrs.get('for'))
                        self.assertIn("btn", optelement.parent.attrs['class'])
                        self.assertEqual(''.join(optelement.parent.stripped_strings), opt[1])
                        # Firefox's caching of radio input field values is expected
                        # to be disabled.
                        self.assertEqual(optelement.attrs.get('autocomplete'), 'off')
                        # A specific keyboard tabbing index for the multi-value field
                        # is not expected to be set.
                        self.assertNotIn('tabindex', optelement.attrs)

        form = self.DummyForm({'the_past_0': 303, 'the_past_1': True})
        result = widget.render(form, 'default', Context({}))
        html = BeautifulSoup(result, 'html.parser')
        for i, data in enumerate(form.data.items()):
            for opt in form.fields['the_past'].fields[i].choices:
                element = html.find(
                    'input', type='radio', attrs={'name': data[0], 'value': str(opt[0])})
                with self.subTest(option=opt, selected=opt[0] == data[1], element=element):
                    self.assertIsNotNone(element)
                    # Each radio input field is expected to be wrapped by a label
                    # styled as a button with text corresponding to the option.
                    self.assertEqual(element.parent.name, 'label')
                    self.assertIn("btn", element.parent.attrs['class'])
                    if opt[0] == data[1]:
                        # A value submitted as form data is expected to be selected.
                        self.assertIn('checked', element.attrs)
                        self.assertIn("active", element.parent.attrs['class'])
                    else:
                        # Any value not submitted as form data is expected to be not selected.
                        self.assertNotIn('checked', element.attrs)
                        self.assertNotIn("active", element.parent.attrs['class'])

    def test_css_classes(self):
        form = self.DummyForm()
        widget = ExpandedMultipleChoice(
            'the_past', wrapper_class="my-container", collapsed=False)
        result = widget.render(
            form, 'default',
            Context({'form_show_labels': True, 'tabindex': 3}),
        )
        html = BeautifulSoup(result, 'html.parser')
        # The form elements are expected to be rendered in a collapsible container
        # corresponding to the form's multi-value field and unfolded by default.
        container_element = html.find('div', id='id_the_past_form_element')
        self.assertIsNotNone(container_element)
        self.assertIn('class', container_element.attrs)
        self.assertIn("collapse", container_element.attrs['class'])
        self.assertIn("in", container_element.attrs['class'])
        self.assertEqual(container_element.attrs.get('aria-expanded'), 'true')
        for i, subfield in enumerate(form.fields['the_past'].fields, start=1):
            element_id = f'id_the_past_option_{i}_form_element'
            with self.subTest(container_id=element_id):
                # Each subfield of the form's multi-value field is expected to be
                # wrapped in a form-group with the specified wrapper CSS class.
                element = html.find('div', id=element_id, class_="form-group")
                self.assertIsNotNone(element)
                self.assertIn("my-container", element.attrs['class'])
                # The control label is expected to be present.
                label_element = element.label
                self.assertIsNotNone(label_element)
                self.assertEqual(label_element.attrs.get('for'), f'id_the_past_{i-1}')
                self.assertIn("control-label", label_element.attrs['class'])
                # When the subfield's CSS class is not specified, only the default
                # classes are expected to be in use.
                subelement = element.find('div', id=f'id_the_past_{i-1}')
                self.assertIsNotNone(subelement)
                self.assertEqual(
                    set(subelement.parent.attrs['class']),
                    set(["controls", "checkbox"]))
                for opt in subfield.choices:
                    optelement = subelement.find(
                        'input',
                        type='radio', attrs={'name': f'the_past_{i-1}', 'value': str(opt[0])})
                    with self.subTest(option=opt, element=optelement):
                        self.assertIsNotNone(optelement)
                        # The specified keyboard tabbing index for the multi-value
                        # field is expected to be set.
                        self.assertEqual(optelement.attrs.get('tabindex'), '3')
                        # The label wrapping each radio input field is expected to
                        # have no hover CSS class.
                        self.assertEqual(optelement.parent.name, 'label')
                        self.assertEqual(
                            optelement.parent.attrs.get('data-hover-class', ""), "")

        widget = ExpandedMultipleChoice(
            'the_past',
            option_css_classes={202: "current-class"},
            option_hover_css_classes={False: "btn-lg", True: "btn-lg"},
            collapsed=True)
        result = widget.render(
            form, 'default',
            Context({
                'form_show_labels': True,
                'label_class': "custom-label",
                'field_class': "custom-controls",
            }),
        )
        html = BeautifulSoup(result, 'html.parser')
        # The form elements are expected to be rendered in a collapsible container
        # corresponding to the form's multi-value field and folded by default.
        container_element = html.find('div', id='id_the_past_form_element')
        self.assertIsNotNone(container_element)
        self.assertIn('class', container_element.attrs)
        self.assertIn("collapse", container_element.attrs['class'])
        self.assertNotIn("in", container_element.attrs['class'])
        self.assertEqual(container_element.attrs.get('aria-expanded'), 'false')
        # The control labels are expected to be rendered with the specified CSS class.
        label_elements = html.select('label.control-label')
        self.assertEqual(len(label_elements), 2)
        for label_element in label_elements:
            self.assertIn("custom-label", label_element.attrs['class'])
        for i, subfield in enumerate(form.fields['the_past'].fields, start=1):
            # The specified subfield's CSS class is expected to be used.
            subelement = html.find('div', id=f'id_the_past_{i-1}')
            self.assertIsNotNone(subelement)
            self.assertEqual(
                set(subelement.parent.attrs['class']),
                set(["custom-controls", "controls", "checkbox"]))
            for opt in subfield.choices:
                option_element = subelement.find(
                    'input',
                    type='radio', attrs={'name': f'the_past_{i-1}', 'value': str(opt[0])})
                with self.subTest(option=opt, element=option_element):
                    self.assertIsNotNone(option_element)
                    # The labels wrapping the radio input fields are expected to have
                    # the specified CSS class(es), corresponding to the options, and
                    # the hover CSS class specified per each option.
                    label_element = option_element.parent
                    self.assertEqual(label_element.name, 'label')
                    if opt[0] in [202]:
                        presence_assertion = self.assertIn
                    else:
                        presence_assertion = self.assertNotIn
                    presence_assertion("current-class", label_element.attrs['class'])
                    self.assertNotIn("custom-label", label_element.attrs['class'])
                    self.assertEqual(
                        label_element.attrs.get('data-hover-class', ""),
                        "btn-lg" if opt[0] in [True, False] else ""
                    )

        widget = ExpandedMultipleChoice('the_past')
        context = Context({'label_class': "custom-label"})
        result = widget.render(
            form, 'default', context,
            extra_context={'inline_class': "select-inline"},
        )
        html = BeautifulSoup(result, 'html.parser')
        # No control label is expected to be rendered by default.
        self.assertEqual(len(html.select('label.control-label')), 0)
        self.assertEqual(len(html.select('label.custom-label')), 0)
        # Unknown values in extra rendering context are not supposed to be used.
        self.assertNotIn('inline_class', context)
        self.assertNotIn('inline_class', result)
        self.assertNotIn("select-inline", result)


@tag('forms', 'widgets')
class MapboxGlWidgetTests(AdditionalAsserts, TestCase):
    widget_class = MapboxGlWidget

    def test_media(self):
        widget = self.widget_class()
        css_media = str(widget.media['css'])
        self.assertRegex(css_media, r'href=".*?/mapbox-gl\.css"')
        js_media = str(widget.media['js'])
        self.assertRegex(js_media, r'src=".*?/mapbox-gl\.js"')
        self.assertRegex(js_media, r'src=".*?/mapbox-gl-widget\.js"')
        self.assertRegex(js_media, r'src=".*?/endpoints/\?format=js\&amp;type=widget"')

    def test_serialize(self):
        widget = self.widget_class()
        self.assertEqual(widget.serialize(None), '')
        self.assertEqual(widget.serialize(""), '')
        self.assertEqual(widget.serialize(GeoPoint()), '')

        result = widget.serialize(GeoPoint(44.342639, -75.924861))
        self.assertSurrounding(result, '{', '}')
        self.assertEqual(
            json.loads(result),
            {'coordinates': [44.342639, -75.924861], 'type': 'Point'}
        )

    def test_render(self):
        widget = self.widget_class(
            {'class': "monkey-patch", 'data-test-z': 99, 'data-test-y': 66, 'data-test-x': 33})
        help_css_class = 'help' if self.widget_class is AdminMapboxGlWidget else 'help-block'
        with override_settings(LANGUAGE_CODE='en'):
            result = widget.render('location_field', None, attrs={'id': 'id_location_field'})
            result = ' '.join(result.split())
            # The template fragment is expected to include the container for the dynamic map.
            self.assertIn('<div id="map"></div>', result)
            # The template fragment is expected to include a fallback for no JavaScript.
            self.assertIn('<noscript>', result)
            # A note about technical requirements is expected.
            self.assertIn("The map requires JavaScript and the WebGL technology.", result)
            # A help text is expected.
            self.assertInHTML(
                f'<p class="{help_css_class}">'
                "Select manually the most suitable point on the map."
                '</p>',
                result)
            self.assertRegex(
                result,
                'id="id_location_field" [^>]*class="[^"]*monkey-patch[^"]*" [^>]*'
                'data-test-z="99" data-test-y="66" data-test-x="33"[^>]*?></'
            )
        with override_settings(LANGUAGE_CODE='eo'):
            result = widget.render(
                'location_field',
                GeoPoint(44.342639, -75.924861),
                attrs={'id': 'id_location_field'})
            result = ' '.join(result.split())
            # A translated note about technical requirements is expected.
            self.assertIn("La mapo necesigas JavaSkripton kaj la teĥnologion WebGL.", result)
            # A translated help text is expected.
            self.assertInHTML(
                f'<p class="{help_css_class}">'
                "Elektu permane la plej taŭgan punkton sur la mapo."
                '</p>',
                result)
            self.assertInHTML(
                html.escape(GeoPoint(44.342639, -75.924861).json),
                result)
            self.assertRegex(
                result,
                'id="id_location_field" .*?>[^<]+?coordinates'
            )

    def test_selectable_zoom(self):
        widget = self.widget_class({'data-selectable-zoom': 3})
        with override_settings(LANGUAGE_CODE='en'):
            result = widget.render('position_field', None, attrs={'id': 'id_position_field'})
            result = ' '.join(result.split())
            # The template fragment is expected to include a note about map scale.
            self.assertIn(
                "It will be possible to register the point when the resolution of the map allows "
                "for visible distances of about 1km or less.",
                result)
            self.assertRegex(result, 'id="id_position_field" [^>]*data-selectable-zoom="3"')
        with override_settings(LANGUAGE_CODE='eo'):
            result = widget.render('position_field', None, attrs={'id': 'id_position_field'})
            result = ' '.join(result.split())
            # The template fragment is expected to include a translated note about map scale.
            self.assertIn(
                "Eblus registri la punkton kiam la distingivo de la mapo permesus distingeblajn "
                "distancojn de ĉirkaŭ 1km aŭ malpli.",
                result)


@tag('admin')
class AdminMapboxGlWidgetTests(MapboxGlWidgetTests):
    widget_class = AdminMapboxGlWidget
