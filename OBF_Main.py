import os.path
import sys
from typing import Dict

from Module import Module
from Project import Project


def print_binds(OO):
    for key, value in OO.items():
        print(f"{key}: {value}")


def get_filename(O0, OO):

    O0O = O0
    O00 = int(O0) if O0.isnumeric() else -1

    if O00 in OO:
        O0O = OO[O00]
    return O0O


def run(O0, OO):

    if O0 == 'FULL':

        for key in OO:
            O0OO = OO[key]
            if O0OO != 'FULL':
                run(O0OO, OO)
        return

    if os.path.isfile(O0):
        O0O0 = Module(O0)
        O0O0.collect_data()
        O0O0.obfuscate()
        #
        O0O0.save()

    else:
        print('project')
        O00O = Project(O0)
        O00O.simple_obfuscation()



if __name__ == "__main__":

    O000 = 0
    OO = {
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

    print(f"PREFIX:{sys.base_exec_prefix}")

    if O000:
        print('!DEBUG!')
        print_binds(OO)
        O0 = get_filename(input('ENTER NAME\n'), OO)
    else:
        print("Enter path to folder/script\n")
        if not sys.argv:
            print(f"No args")
            exit(0)
        O0 = sys.argv[0]


    run(O0, OO)
