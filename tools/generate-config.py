import configparser, json
from pathlib import Path

print("This tool generates a config.ini from the base JSON config format.")

# path = Path(input("Path to config-base.json: "))
path = 'config-base.json'

with open(path, 'r') as f:
    config_base = json.load(f)

ini = configparser.RawConfigParser(allow_no_value=True)

for section in config_base:
    ini.add_section(section)
    for entry in config_base[section]:
        if 'description' in config_base[section][entry]:
            ini.set(section,
                    '; ' + config_base[section][entry]['description'])
        if entry != 'meta':
            value = config_base[section][entry]['value']
            print(f'{entry} : {type(value)} : should be {config_base[section][entry]["type"]}')
            if isinstance(value, bool):
                value = str(value).lower()
            else:
                value = str(value)
            ini.set(section,
                    entry,
                    value)

with open('config.ini', 'w') as config_file:
    ini.write(config_file)
print("written.")
