import importlib, inspect
m = importlib.import_module('auth')
print('module:', m)
print('file:', getattr(m, '__file__', None))
print('has AuthManager:', hasattr(m, 'AuthManager'))
print('names with Auth:', [n for n in dir(m) if 'Auth' in n])
# Show top-level source snippet
print('\n--- source preview ---')
with open(m.__file__, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i < 120:
            print(f'{i+1:03}:', line.rstrip())
        else:
            break
