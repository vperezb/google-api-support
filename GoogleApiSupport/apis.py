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
    }
}


@functools.lru_cache()
def get_api_config(api_name):
    return api_configs[api_name]

def all_scopes():
    return [ data['scope'] for __placeholder, data in api_configs.items() ]
