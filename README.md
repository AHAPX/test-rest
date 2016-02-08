# test-rest
client-side RESTful test app

## Description
Automatic tool for testing rest api. You have to write [configuration file](#Test-config-file)
Results printed in console.

## Requirements
- [python 3.3+](https://www.python.org/download/releases/3.3.0/)

## Installation
```bash
$ git clone https://github.com/AHAPX/test-rest
$ cd test-rest
$ pip install -r requirements.txt
```

## Usage
```bash
$ python main.py testfile.yml
```

### Test config file
Test file format can be:
- [yaml](http://www.yaml.org/start.html)

#### yaml
Example:
```yml
url: http://example.com/
method: get
code: 200
handler: dict
actions:
    - action1:
        url: /account/
        steps:
            - step1:
                url: welcome
                result: {message: Welcome}
                skip_errors: True
            -
                url: index.html
                code: 404
    - action2:
        url: /forum/
        step2:
            -
                url: comments
                method: post
                data: {text: Hello}
                code: 200
                result: {rc: True, number: None}
                handler: dict(only_keys=True, level=1)
```

File has 3 levels:

1. **root** with required element *actions*, which has action list.
2. **action** must have required element *steps*
3. **step** is description of api test

Each level can have fields:
- url - required field for step and root, not required for action
- method - rest api method, default - GET
- data - sent data if method == POST
- code - status code of request which you expect, default - 200
- result - data which you expect to get
- handler - [handler of result](#handlers)
- skip_errors - do not show errors, only warnings

#### Handlers
Hanlder compares expected resut with actual response.
Names of hanlders:
- base - compares data straightforward, like a == b
- list - default behaviour same as base, if you want to compare lists independently order use list(any_order=True)
- dict - default behaviour same as base, if you want to compare keys, but not values, use dict(only_keys=True, level=1). level argument shows how deep compare dicts inside, i.e. {a: {b: {c: {d: 1}}}}

## Testing
```bash
$ python -m unittest
```
