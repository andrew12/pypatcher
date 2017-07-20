from __future__ import print_function

from functools import partial
import sys
import yaml

from qtpy.QtWidgets import *

def read(fp, offset, size):
    fp.seek(offset)
    data = fp.read(size)
    assert len(data) == size, "read %d bytes, expected %d" % (len(data), size)

def write(fp, offset, data):
    fp.seek(offset)
    fp.write(data)

class PatchCheckBox(QCheckBox):
    def __init__(self, group, mod):
        QCheckBox.__init__(self, mod['name'])
        self.group = group
        self.patches = mod['patches']
        self.clicked.connect(self.doPatch)

    def doPatch(self, checked):
        for patch in self.patches:
            self.group.write(patch['offset'], patch[checked])

class PatchRadio(QRadioButton):
    def __init__(self, union, patch):
        QRadioButton.__init__(self, patch['name'])
        self.union = union
        self.patch = patch
        self.clicked.connect(self.doPatch)

    def doPatch(self, state):
        self.union.write(self.patch)

class PatchUnion(QGroupBox):
    def __init__(self, group, mod):
        QGroupBox.__init__(self, mod['name'])
        self.mod = mod
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        for patch in mod['patches']:
            radio = PatchRadio(self, patch)
            self.layout.addWidget(radio)

    def write(self, patch):
        self.group.write(self.mod['offset'], patch)

class PatchGroup(QGroupBox):
    def __init__(self, filename, mods):
        # XXX - read in the file data
        filename += '.dll'
        QGroupBox.__init__(self, filename)
        self.filename = filename
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        for mod in mods:
            if 'type' in mod and mod['type'] == 'union':
                self.layout.addWidget(PatchUnion(self, mod))
            else:
                self.layout.addWidget(PatchCheckBox(self, mod))

    def write(self, offset, patch):
        # XXX - update the stored file data
        print(self.filename, offset, patch)
        # This could instead seek to the offset and write the data
        # while the patcher is running

    def __del__(self):
        # XXX - write out data
        pass

class Patcher(QWidget):
    def __init__(self, files):
        QWidget.__init__(self)
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
