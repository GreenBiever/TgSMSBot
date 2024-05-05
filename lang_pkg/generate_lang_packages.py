import click
from xml.etree import ElementTree
from translate import translate, CountriesEnum, merge_lang_pkg, write_tmp_tree

path = r'lang_data.xml'


group = click.group()
@group
def default():
    pass

@default.command()
def generate():
    '''Generate XML file with all languages data.
    Text is taken from lang_pkg.source_data.source dict'''
    tree = write_tmp_tree()
    for lang, text_tree in zip(CountriesEnum, translate(ElementTree.tostring(tree.getroot()).decode("utf-8"),
                                                        list(CountriesEnum), CountriesEnum.russian)):
        if lang == CountriesEnum.russian:
            continue
        new_tree = ElementTree.ElementTree(
            ElementTree.fromstring(text_tree.replace('title="RU"', f'title="{lang.value}"')))
        merge_lang_pkg(tree, new_tree, lang=lang.value, rewrite=True)
    tree.write("lang_data.xml", encoding='utf-8')


@default.command()
@click.argument('lang')
@click.argument('file')
@click.option('--rewrite', is_flag=True, help='Rewrite text if this text exsists in main XML')
def merge_file(lang: str, file: str, rewrite: bool = False):
    '''Connect new file with lang data to main XML file manually'''
    tree = ElementTree.parse(file)
    main_tree = ElementTree.parse(path)
    merge_lang_pkg(main_tree, tree, lang, rewrite)
    main_tree.write(path, encoding='utf-8')


if __name__ == '__main__':
    default.main()