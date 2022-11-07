import functools

api_configs = {
    "slides": {
        "scope": "https://www.googleapis.com/auth/presentations",
        "build": "slides",
        "version": "v1"
    },
    "drive": {
        "scope": "https://www.googleapis.com/auth/drive",
        "build": "drive",
        "version": "v3"
    },
    "sheets": {
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "build": "sheets",
        "version": "v4"
    },
    "docs": {
        "scope": "https://www.googleapis.com/auth/documents",
        "build": "docs",
        "version": "v1"
    },
    "tasks": {
        "scope": "https://www.googleapis.com/auth/tasks",
        "build": "tasks",
        "version": "v1"
    },
    "forms": {
        "scope": "https://www.googleapis.com/auth/forms",
        "build": "forms",
        "version": "v1"
    },
    "gmail": {
        "scope": "https://www.googleapis.com/auth/gmail.modify",
        "build": "gmail",
        "version": "v1"
    },
    "calendar": {
        "scope": "https://www.googleapis.com/auth/calendar",
        "build": "calendar",
        "version": "v3"
    }
}


@functools.lru_cache()
def get_api_config(api_name):
    return api_configs[api_name]

def all_scopes():
    return [ data['scope'] for __placeholder, data in api_configs.items() ]
