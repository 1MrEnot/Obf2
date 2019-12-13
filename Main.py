import os.path
import sys
from typing import Dict

from Module import Module
from Project import Project


def print_binds(binds: Dict[int, str]):
    for key, value in binds.items():
        print(f"{key}: {value}")


def get_filename(path: str, binds: Dict[int, str]) -> str:

    res: str = path
    code = int(path) if path.isnumeric() else -1

    if code in binds:
        res = binds[code]
    return res


def run(path: str, binds: Dict[int, str]):

    if path == 'FULL':

        for key in binds:
            command = binds[key]
            if command != 'FULL':
                run(command, binds)
        return

    if os.path.isfile(path):
        module = Module(path)
        module.collect_data()
        module.obfuscate()
        # print(module.tree)
        module.save()

    else:
        project = Project(path)
        project.simple_obfuscation()



if __name__ == "__main__":

    DEBUG = 0
    binds = {
        0: 'FULL',
        1: 'Main.py',
        2: 'Test.py',
        3: 'Test2.py',
        4: 'Transformers.py',
        5: 'Module.py',
        6: 'Project.py',
        7: r'C:\Users\MaX\PycharmProjects\TestProject',
        8: r'C:\Users\MaX\PycharmProjects\Insatity',
        9: r'C:\Users\MaX\PycharmProjects\Obfuscator',
        10: r'C:\Users\MaX\PycharmProjects\ObfuscatorV2'
    }

    if DEBUG:
        print('!DEBUG!')
        print_binds(binds)
        path = get_filename(input('ENTER NAME\n'), binds)
    else:
        if not sys.argv:
            print(f"No args")
            exit(0)
        path = sys.argv[1]


    run(path, binds)

print("done")
