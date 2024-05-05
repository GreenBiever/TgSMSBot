import requests
import json
from enum import Enum
import re
import html
from xml.etree import ElementTree

try:
    from lang_pkg.source_data import source
except ModuleNotFoundError:
    from source_data import source


class CountriesEnum(Enum):
	english = "EN"
	russian = 'RU'
	german = "DE"
	arabic = "AR"
	chinese = "ZH"
	polish = "PL"

def translate(text: str, target: CountriesEnum | list[CountriesEnum], source: CountriesEnum) -> str:
    url = "https://microsoft-translator-text.p.rapidapi.com/translate"

    querystring = {"to[0]": target.value if isinstance(target, CountriesEnum)
                  else ','.join([t.value for t in target]),
                  "api-version":"3.0","from": source.value,
                  "profanityAction":"NoAction",
                  "textType":"html"}

    payload = [{ "Text": html.unescape(text) }]
    headers = {
	    "content-type": "application/json",
	    "X-RapidAPI-Key": "aaf7c33ce8mshf7cce6904d02c30p1c9bbdjsnad3b87c995c5",
	    "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
    }
    response = requests.post(url, json=payload, headers=headers, params=querystring)
    data = response.json()
    return [data['text'] for data in data[0]['translations']]


def _serialize(text: str) -> tuple[str, tuple[str]]:
    '''Serialize text with f-string

    >>>serialize("Hello, {name}!")
    ("Hello, {}", ("name"))
    '''
    pattern = '{\w+}'
    args = [s[1:-1] for s in re.findall(pattern, text)]
    text = re.sub(pattern, '{}', text)
    return text, args

def write_tmp_tree():
    '''write base xml that may be used in API
    "Node "lang" will be generated 
    with following params: <lang title="ru">text...</lang>'''
    tree = ElementTree.ElementTree(ElementTree.fromstring("<data></data>"))
    root = tree.getroot()
    for key, text in source.items():
        if isinstance(text, str):
            text, args = _serialize(text)
            e = ElementTree.SubElement(root, 'text', {'name': key, 'args': ' '.join(args)})
            lang = ElementTree.SubElement(e, 'lang', {'title': 'RU'})
            lang.text = text
        elif isinstance(text, list):
            e = ElementTree.SubElement(root, key)
            for item in text:
                elem = ElementTree.SubElement(e, 'text', {'name': item})
                lang = ElementTree.SubElement(elem, 'lang', {'title': 'RU'})
                lang.text = item
    return tree


def merge_lang_pkg(main_tree: ElementTree.ElementTree,
                  merged_tree: ElementTree.ElementTree, lang: str, rewrite: bool = False):
    root = main_tree.getroot()
    merged_root = merged_tree.getroot()
    for text_element in merged_root.findall('.//text'):
        name = text_element.attrib.get('name')
        if (elem := root.find(f'.//text[@name="{name}"]')) is not None:
            if elem.find(f'.//lang[@title="{lang}"]') is None:
                new_elem = ElementTree.SubElement(elem, 'lang', {'title': lang})
                merged_element = text_element.find(f'lang[@title="{lang}"]')
                if merged_element is None:
                    ElementTree.dump(text_element)
                    raise ElementTree.ParseError(f"Some node 'text' in merged tree \
dont have child node 'lang' with title={lang}")
                new_elem.text = merged_element.text
            elif rewrite:
                xpath = f'.//lang[@title="{lang}"]'
                elem.find(xpath).text = text_element.find(xpath).text

def parse_lang_data(path: str = r'C:\Users\vn264\Desktop\sms_bot\lang_pkg\lang_data.xml') -> dict[str, dict[str,str]]:
    '''Load language data from XML file.
    :return: Dict with all lnaguages and all texts. Type of dict:
    {"start_text": {"ru: "Привет", "en": "Hello", ...}, ...}
    '''
    tree = ElementTree.parse(path)
    root = tree.getroot()
    lang_data = {}
    for text in root.findall('.//text'):
        name = text.attrib.get('name')
        args = text.attrib.get('args', '').split(' ')
        lang_data[name] = {}
        for lang in text.findall('.//lang'):
            text = lang.text.strip("\n").strip('\t').strip('\r')
            text = text.replace('\t', '')  # Warning
            for arg in args:
                text = text.replace("{}", f'{{{arg}}}', 1)
            lang_data[name][lang.attrib.get('title')] = text
    return lang_data

lang_data = parse_lang_data()