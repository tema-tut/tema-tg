#!/usr/bin/env python
# -*- coding: utf-8
# Copyright (c) 2006-2010 Tampere University of Technology
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from distutils.core import setup
from distutils.command.build_scripts import build_scripts,first_line_re
from distutils.command.bdist_wininst import bdist_wininst
from distutils.dist import Distribution

from shutil import copyfile,rmtree
from tempfile import mkdtemp
import os
import glob

class Distribution_extended(Distribution):
    def __init__ (self, attrs=None):
        self.add_prefix = False
        self.remove_prefix = False
        Distribution.__init__(self,attrs)

class bdist_wininst_extended(bdist_wininst):
    def run(self):
        self.distribution.add_prefix = True
        bdist_wininst.run(self)
        
class build_scripts_add_extension(build_scripts):

    def _transform_script_name(self,script_name):
        script_base = os.path.basename(script_name)
        filu = open(script_name,'r')
        firstline = filu.readline()
        filu.close()
        if firstline:
            match = first_line_re.match(firstline)
        else:
            match = None
                    
        file_name = script_base
        if match:
            if self.distribution.add_prefix and not script_base.endswith(".py"):
                file_name = "%s.py" % script_base
            if self.distribution.remove_prefix and script_base.endswith(".py"):
                file_name = script_base[:-3]


        if not file_name.startswith("tema."):
            file_name = "tema.%s" % file_name

        return file_name

    def run(self):
        # Not in posix system. Add prefix .py just to be sure
        if os.name != "posix":
            self.distribution.add_prefix = True
        # Remove .py prefix in posix. 
        elif os.name == "posix" and not self.distribution.add_prefix:
            self.distribution.remove_prefix = True

        try:
            tempdir = mkdtemp()
            new_names = []
            for script in self.scripts:
                new_name = os.path.join(tempdir,self._transform_script_name(script))
                new_names.append(new_name)
                copyfile(script,new_name)

            self.scripts = new_names
            build_scripts.run(self)
        finally:
            if os.path.isdir(tempdir):
                rmtree(tempdir)

try:
    input_h = open("LICENCE",'r')
    LICENCE=input_h.read()
finally:
    input_h.close()

VERSION='3.2'

def get_scripts():
    
    scripts = glob.glob("Validation/simulation/*.py")
    log_tools = glob.glob("Validation/loghandling/*.py")
    if "Validation/loghandling/avgofdats.py" in log_tools:
        log_tools.remove("Validation/loghandling/avgofdats.py")
    scripts.extend(log_tools)
    scripts.append("Validation/viewer/model2dot.py")
    scripts.append("ModelUtils/runmodelpackage.py")
    scripts.append("ModelUtils/actionlist.py")
#    scripts.append("TemaLib/MockSUT/mocksut.py")
    scripts.extend(glob.glob("Validation/analysis/*.py"))
    modelutils = glob.glob("TemaLib/tema/modelutils/*.py")
    modelutils.remove("TemaLib/tema/modelutils/__init__.py")
    scripts.extend(modelutils)
    scripts.append("TemaLib/tema/model/model2lsts.py")
    scripts.append("TemaLib/tema/eini/mdm2svg.py")
    scripts.append("TemaLib/tema/packagereader/packagereader.py")
    scripts.append("TemaLib/tema/ats4appmodel/ats4appmodel2lsts.py")
    scripts.append("TemaLib/tema/filter/filterexpand.py")
    scripts.append("TemaLib/tema/variablemodels/variablemodelcreator.py")
    scripts.append("TemaLib/tema/testengine/testengine.py")
    
    return scripts

def get_packages(start_path):
    for root,dirs,files in os.walk(start_path):
        for filename in files:
            if filename == "__init__.py":
                yield root.split(start_path + os.sep,1)[1].replace("/",".")

def get_manpages():
    man_pages = glob.glob("Docs/man/man1/*.1")
    return man_pages

packages_list = list(get_packages("TemaLib"))
if "ToolProxy" in packages_list:
    packages_list.remove("ToolProxy")

scripts_list = get_scripts()

manpages_list = get_manpages()

setup(name='tema-tg',
      provides=['tema',],
      license=LICENCE,
      version=VERSION,
      description='TEMA Test engine',
      author="Tampere University of Technology, Department of Software Systems",
      author_email='teams@cs.tut.fi',
      url='http://tema.cs.tut.fi',
      package_dir = {"" : "TemaLib" },
      data_files=[('share/man/man1', manpages_list),
                  ('lib/tema-tg/gui_interface',['gui_interface/tema.start_engine','gui_interface/tema.list_sessions','gui_interface/tema.kill_engine'])],
      packages=packages_list,
      package_data={"tema.modelutils" : ["pcrules/Generic*","makefiles/GNUmakefile*"]},
      scripts=scripts_list,
      cmdclass={"build_scripts"  : build_scripts_add_extension, "bdist_wininst" : bdist_wininst_extended },
      distclass=Distribution_extended,
     )
