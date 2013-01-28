#!/usr/bin/env python
#-*- coding: iso-8859-1 -*-
# Copyright (c) 2011 Heikki Virtanen, Tampere University of Technology
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


r"""

      tema batch [--help|--info|--exec]

Tool for creating a configured test model and test engine parameters.

Tema batch reads input from stdin and writes the configured test model
in directory 'TestModel' and the command line parameters of the test
engine into the file 'engine.prms'. It is assumed that the model
exported from ModelDesigner resides in directory 'Model'.

Input is line oriented.  Each line describes either a system under test
or one command line switch for the test engine.

The test target definition contains semicolon (;) separated entries.
The first entry is the name of the device under test and the rest are
the names of the applications to be tested.

The test engine command line switch starts with two hyphen (--) and those are
documented in the context of the test engine.  There are a few exceptions:
- Used model is added automatically.
- An empty coveragereq is added if randomguidance is used.
- If --testdata option is not included, datatables required by the model
  are included in the file 'engine.prms'.
- If testadapter is used, the model is added as adapter argument.

Empty lines and lines starting with the number sing (#) are ignored.

Example of input:

Emulator;Gallery;Camera
Jacob;Messaging
--coveragereq=
--guidance=tabuguidance
--guidance-args=numtabuactions:infinite
--adapter=testadapter
--testdata=nodata

* Options

--help	Print this help and exit
--info	Print some information which helps writing required input, and exit
--exec	Addition to constructing the configuration, start testengine as well.

Without any option, input is read and the configured model and the
test engine parameters are generated. In this case, the configured test
can be run with a command:

  cd TestModel && cat ../engine.prms | xargs -d "\n" tema testengine

"""


import sys
import os
import stat
import subprocess
import urllib
import zipfile
import tema.packagereader.packagereader as packagereader
import tema.modelutils.generatetestconf as generatetestconf
import tema.modelutils.composemodel as composemodel

class Parameters:
    pass

def pkgr_cmd(*args):
    return ("tema", "packagereader", Parameters.domain_file ) \
           + tuple(args)

def set_domain_file_name():
    Parameters.domain_file=None
    Parameters.model_dir = "Model"
    files = os.listdir(Parameters.model_dir)
    for name in files:
        if name.find(".mdd") > 0 :
            Parameters.domain_file = os.path.join(Parameters.model_dir,name)
            break
    if not Parameters.domain_file:
        raise SystemExit("Model directory do not exits")
    Parameters.pkg_reader=packagereader.Reader(Parameters.domain_file)
    return None


def do_pkg_query(*args):
    if Parameters.domain_file :
        reader = Parameters.pkg_reader
        try:
            data = reader.getValue(args[0],args[1:])
        except:
            raise SystemExit("Package reader failed")
        return data.strip().split("\n")
    raise SystemExit("Domain is not set")

def set_domain_name():
    Parameters.domain_name=do_pkg_query("name")[0]
    if not Parameters.domain_name :
        raise SystemExit("There is no proper domain description")

def set_unit_components(obj, prod, unit):
    pass

def dt_list(dts):
    res = list()
    for dt in dts :
        if Parameters.datatables.has_key(dt) :
            res.append(Parameters.datatables[dt])
        else:
            pass #res.append(dt)
    return res

def set_product_units(obj, prod):
    for unit in do_pkg_query("concurrentunits", prod) :
        obj[unit] = do_pkg_query("components", prod, unit)
#         for compo in obj[unit]:
#             dts = do_pkg_query("datarequirement", unit, compo)
#             if dts and dts[0] :
#                 print unit, compo, ":",\
#                       repr( dt_list(dts) )

def set_domain_products():
    Parameters.datatables=dict()
    dts=do_pkg_query("datatables")
    for dt in dts :
        if len(dt) < 1 :
            continue
        dt_name = do_pkg_query("logicalname", dt)[0]
        Parameters.datatables[dt_name] = dt
        # print dt,":", dt_name
    Parameters.products=dict()
    prods = do_pkg_query("products")
    # print " ".join(prods)
    Parameters.dev_map = dict()
    for prod in prods :
        tmp_o = dict()
        Parameters.products[prod] = tmp_o
        tmp_o['units']=dict()
        set_product_units( tmp_o['units'] , prod )
        tmp_o['devs']=do_pkg_query("devices", prod)
        for dev in tmp_o['devs'] :
            Parameters.dev_map[dev] = prod
    #print repr(Parameters.products)


def quoted_string(sss):
    temppi = urllib.quote(sss)
    idx = temppi.find('%')
    while 0 <= idx :
        temppi = temppi[:idx]+temppi[idx:idx+3].lower()+temppi[idx+3:]
        idx = temppi.find('%',idx+1)
    return temppi

def append_lstses(lstses, unit, comps):
    lstses.extend( [ quoted_string("%s - %s.lsts" % (unit, cm) ) \
                     for cm in comps ] )
    return None

def get_components( prod, unit, lstses, datatbls):
    comps = do_pkg_query("components", prod, unit)
    append_lstses(lstses, unit, comps)

    for compo in comps:
        dts = do_pkg_query("datarequirement", unit, compo)
        if dts and dts[0] :
            datatbls.update(dt_list(dts))

    return lstses

def get_datatables(dts):
    return [ ( "%s.td" % dt ).replace(' ', '%20') for dt in dts if len(dt) > 0 ]

class TestTarget:
    def __init__(self, trg):
        self.target_id = trg
        self.product = Parameters.dev_map[trg]
        if len(self.target_id) < 1 :
            self.target_tag=self.product
        else:
            self.target_tag=self.target_id
        self.apps= list()

    def addApp(self, app_name):
        self.apps.append(app_name)



def get_testdata(dts):
    return ",".join( [ ("file:%s.td" % dt ).replace(' ', "%20") for dt in dts ] )

def write_config(*targets):
    products = set()
    datatables = set()
    with file("testiconffi.conf", "w") as conffi :
        print >> conffi, "[targets: type]"
        for trg in targets:
            print >> conffi, "%s: %s" % (trg.target_tag, trg.product)
            products.add(trg.product)
            datatables.add(trg.target_id)
        print >> conffi, "[targets: actionmachines[]]"
        for trg in targets:
            lstses = list()
            for unt in trg.apps :
                get_components( trg.product, unt, lstses, datatables )
            print >> conffi, "%s: %s" % ( trg.target_tag,
                                          ", ".join( lstses ) )
        print >> conffi, "[data: names[]]"
        print >> conffi, "datatables:",\
              ", ".join( get_datatables(datatables) )
        print >> conffi, "localizationtables:",\
              ",".join( [ ("%s.csv" % p ) for p in products ] )
    return datatables

def write_params(defined, datatables):
    with file("engine.prms", "w") as prms :
        print >> prms, "--model=parallellstsmodel:combined-rules.ext"
        for ent in defined:
            print >> prms, ent
        if Parameters.emit_dts :
            print >> prms, "--testdata=%s" % get_testdata(datatables)

def check_apps(sut, apps):
    if sut in Parameters.dev_map.keys():
        prod = Parameters.dev_map[sut]
        units = set(Parameters.products[prod]['units'].keys())
        return (len(apps)>0) and (set(apps) <= units)
    else:
        return False

def modelled_apps(sut):
    if sut in Parameters.dev_map.keys():
        prod = Parameters.dev_map[sut]
        return (prod, Parameters.products[prod]['units'].keys())
    else:
        return ("No such device!", list())



if "__main__" == __name__ :

    if "--help" in sys.argv :
        print __doc__
        raise SystemExit(0)

    Parameters.modelDir = "Model"
    Parameters.modelDirExists = False
    try:
        Parameters.modelDirExists = stat.S_ISDIR(os.stat(Parameters.modelDir).st_mode)
    except:
        pass

    if not Parameters.modelDirExists :
        for param in sys.argv:
            if (param.find("--") != 0) and (param.find(".zip") > 1) :
                archive=None
                try:
                    os.mkdir(Parameters.modelDir)
                    archive=zipfile.ZipFile(param,'r')
                    archive.extractall(path=Parameters.modelDir)
                finally:
                    if archive :
                        archive.close()
    set_domain_file_name()
    set_domain_name()
    set_domain_products()

    if "--info" in sys.argv :
        print "Domain name:", Parameters.domain_name
        print "Defined devices: (name, product)"
        mappi = Parameters.dev_map
        print "\n".join([ "\t%s, %s" % (a, mappi[a]) for a in mappi.keys()])
        print "Applications per product:"
        for prod in Parameters.products.keys():
            units = Parameters.products[prod]['units']
            print "\t"+prod+':', ", ".join(units.keys())
        raise SystemExit(0)

    Parameters.emit_dts=True

    targets=list()
    engine_prms=list()

    for conf_line in sys.stdin:
        entry = conf_line.strip().lstrip()
        if len(entry) == 0:
            continue
        if entry.find('#') == 0 :
            continue

        modelvardefs=None

        if entry.find("--") == 0 :
            if entry.find("--modelvardefs") == 0 :
                idx=entry.find("=")
                modelvardefs=entry[idx+1:].strip()
            else:
                engine_prms.append(entry)
            if entry.find("--testdata") == 0 :
                Parameters.emit_dts = False
            if entry.find("testadapter") > 0 :
                engine_prms.append("--adapter-args=model:combined-rules.ext")
            if entry.find("randomguidance") > 0 :
                engine_prms.append("--coveragereq=")
            if entry.find("guiguidance") > 0 :
                engine_prms.append("--adapter-args=")

        else :
            items=entry.split(';')
            sut,apps = items[0],items[1:]
            if check_apps(sut, apps) :
                ttg = TestTarget(sut)
                targets.append(ttg)
                for app in apps :
                    ttg.addApp(app)
            else :
                print "Error: Requested applications do not exist in model"
                print sut+':', ", ".join(items[1:])
                prod,modelled = modelled_apps(sut)
                print prod+':', ", ".join(modelled)
                raise SystemExit(1)

    used_datatables = write_config(*targets)
    write_params(engine_prms, used_datatables)

    generatetestconf.generatetestconf("Model", "testiconffi.conf", "TestModel",
                                      modelvardefs)

    # composemodel.compose_model("TestModel", "compose.conf")
    # compose_model is out of date: It does not work with parametriced models.
    # using command: tema do_make
    # this is somewhat gludge. It should make difference between
    # "tema <command>" and "tema.<command>"
    try:
        os.chdir("TestModel")
        cmdline=["tema", "do_make"]
        make=subprocess.Popen(cmdline)
        res=make.wait()
    finally:
        os.chdir("..")


    print "\nDone: Configured test model in directory TestModel"

    res = 0
    if "--exec" in sys.argv :
        cmdline = list()
        with file("engine.prms","r") as opts:
            cmdline = opts.read().strip().split("\n")
        cmdline[:0]= ["tema", "testengine"]
        print " ".join(cmdline)
        os.chdir("TestModel")
        tg= subprocess.Popen(cmdline)
        res=tg.wait()
        os.chdir("..")
    raise SystemExit(res)
