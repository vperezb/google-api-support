import json
import yaml


def open_file(filename, mode):
    with open(filename, mode) as openfile:
        return openfile.read()


def read_yml(filename):
    with open(filename, 'r') as ymlfile:
        return yaml.load(ymlfile)


def read_json_file(filename, mode):
    return json.loads(open_file(filename, mode))


def seconds_to_minutes_and_seconds(seconds):
    output = ''
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if minutes:
        output = '{:1}m'.format(int(minutes))
    output += '{:02}s'.format(int(seconds))
    return output