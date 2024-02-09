from configparser import ConfigParser
import os


DEFAULT_FILENAME = 'default_config.ini'
FILENAME = 'config.ini'
config = ConfigParser()

if os.path.exists(FILENAME):
    config.read(FILENAME)
elif os.path.exists(DEFAULT_FILENAME):
    config.read(DEFAULT_FILENAME)
else:
    print("Файл 'default_config.ini' не найден, создайте один из файлов: 'default_config.ini' \
или 'config.ini' и внесите в него соответствующие значения")
    raise SystemExit
