import platform

arch = platform.architecture()
print(f'Architecture: {arch}')

mach = platform.machine()
print(f'Machine: {mach}')

node = platform.node()
print(f'Network Node: {node}')

myplatform = platform.platform()
print(f'Platform: {myplatform}')

release = platform.release()
print(f'Release: {release}')

system = platform.system()
print(f'System: {system}')

uname = platform.uname()
print(f'Uname: {uname}')