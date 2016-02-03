from loaders import YAMLLoader


loader = YAMLLoader('test.yaml')
for action in loader.load():
    action.run()
