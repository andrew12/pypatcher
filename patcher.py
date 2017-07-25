from __future__ import print_function

from functools import partial
import os
import sys
import yaml
import mmap

from PyQt5.QtWidgets import *

def read(fp, offset, size):
    fp.seek(offset)
    data = fp.read(size)
    assert len(data) == size, "read %d bytes, expected %d" % (len(data), size)

class PatchCheckBox(QCheckBox):
    def __init__(self, group, mod):
        self.name = mod['name']
        QCheckBox.__init__(self, self.name)
        self.group = group
        self.patches = mod['patches']
        if self.check():
            self.setChecked(True)
        self.clicked.connect(self.doPatch)

    def check(self):
        status = None
        for patch in self.patches:
            offset = patch['offset']
            on = bytes(patch[True])
            off = bytes(patch[False])
            assert len(on) == len(off)
            if self.group.mmap[offset:offset+len(off)] == off:
                if status is None:
                    status = False
                elif status != False:
                    print('on/off mismatch')
                    return
            elif self.group.mmap[offset:offset+len(on)] == on:
                if status is None:
                    status = True
                elif status != True:
                    print('on/off mismatch')
                    return
            else:
                print('neither on nor off')
                return
        return status

    def validate(self):
        status = self.check()
        if status == True:
            print(self.name, 'is enabled')
        elif status == False:
            print(self.name, 'is disabled')
        else:
            return '%r not found' % self.name

    def doPatch(self, checked):
        for patch in self.patches:
            self.group.write(patch['offset'], patch[checked])

class PatchRadio(QRadioButton):
    def __init__(self, union, patch):
        QRadioButton.__init__(self, patch['name'])
        self.union = union
        self.patch = bytes(patch['patch'])
        if self.check():
            self.setChecked(True)
        self.clicked.connect(self.doPatch)

    def check(self):
        return self.union.group.mmap[self.union.offset:self.union.offset+len(self.patch)] == self.patch

    def doPatch(self, state):
        self.union.write(self.patch)

class PatchUnion(QGroupBox):
    def __init__(self, group, mod):
        self.group = group
        self.name = mod['name']
        self.offset = mod['offset']
        self.patches = mod['patches']
        QGroupBox.__init__(self, self.name)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        for patch in self.patches:
            radio = PatchRadio(self, patch)
            self.layout.addWidget(radio)

    def validate(self):
        for p in self.patches:
            patch = p['patch']
            if self.group.mmap[self.offset:self.offset+len(patch)] == bytes(patch):
                print(self.name, 'has', p['name'])
                return
        return '%r not found' % self.name

    def write(self, patch):
        self.group.write(self.offset, patch)

class PatchGroup(QGroupBox):
    def __init__(self, filename, mods):
        filename += '.dll'
        QGroupBox.__init__(self, filename)
        self.fileno = os.open(filename, os.O_RDWR | os.O_BINARY)
        self.mmap = mmap.mmap(self.fileno, 0)
        self.filename = filename
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.mods = []
        for mod in mods:
            if 'type' in mod and mod['type'] == 'union':
                o = PatchUnion(self, mod)
            else:
                o = PatchCheckBox(self, mod)
            self.mods.append(o)
            self.layout.addWidget(o)
        if self.validate():
            print('DLL loaded successfully!')

    def validate(self):
        errors = []
        for mod in self.mods:
            error = mod.validate()
            if error:
                errors.append(error)
        if errors:
            QMessageBox.critical(self, 'Error', '\n'.join(errors))
        return not errors

    def write(self, offset, patch):
        self.mmap[offset:offset+len(patch)] = bytes(patch)
        print(self.filename, offset, patch)
        self.mmap.flush()

    def __del__(self):
        self.mmap.flush()
        self.mmap.close()
        os.close(self.fileno)

class Patcher(QWidget):
    def __init__(self, files):
        QWidget.__init__(self)
        self.setWindowTitle('DLL Patcher')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        for filename, mods in files.items():
            self.layout.addWidget(PatchGroup(filename, mods))

if __name__ == '__main__':
    with open('sdvx.yml', 'r') as f:
        mods = yaml.load(f)

    app = QApplication(sys.argv[1:])
    win = Patcher(mods)
    win.show()
    app.exec()
