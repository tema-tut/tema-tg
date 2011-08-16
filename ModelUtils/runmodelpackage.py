#!/usr/bin/env python
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

"""Starts testengine using the given modelpackage.

Usage: tema.runmodelpackage MODELPACK.zip|MODELPACKDIR [OPTIONS]
The modelpackage is extracted, configured, composed, and ran with testengine.

Run runmodelpackage.py -h for help.
"""

import sys, os, optparse, zipfile, urllib, re, shutil

from tema.packagereader.packagereader import Reader
import tema.data.datareader as datareader
import tema.modelutils.generatetestconf as generatetestconf
import tema.modelutils.composemodel as composemodel

class RunModelPackageFailed(Exception):
    pass

def parseArgs(cmdArgs):
    # Check if we have guiguidance and guiadapter available
    try:
        import tema.guidance.guiguidance as guiguidance
        guidancedefault="guiguidance"
    except ImportError,e:
        guidancedefault="randomguidance"
    try:
        import tema.adapter.guiadapter as guiadapter
        adapterdefault="guiadapter"
    except ImportError,e:
        adapterdefault="socketserveradapter"

    usage="runmodelpackage.py MODELPACK.zip|MODELPACKDIR [OPTIONS]\n\n\
MODELPACK.zip is something you can export from ModelDesigner\n\
It will be extracted to MODELPACK directory.\n\n\
Eg. runmodelpackage.py modelpackage.zip\n\
                       --devices=\"MyDevice\"\n\
                       --runonport=9090\n\
                       --guidance=randomguidance\n\n\
By default: using guiguidance, guiadapter (if available)\n\
and all the devices found in the package.\n\n\
-h for help."

    op = optparse.OptionParser(usage=usage)

    op.add_option('--runonport', metavar='PORT',
        help="Shortcut to start socketserveradapter on the given port. "+
             "Overrides --adapter and --adapter-args.")

    op.add_option('--devices',
        help="The name(s) of the device(s) to use in the test run. "+
                  "Space-separated. Locale can be given with separator ':' "+
                  "Default: all the devices in the package. " + 
                  "Example: 'Ian:en Emulator'")

    op.add_option('--products',
        help="The name(s) of the product(s) to use in the test run. "+
             "Space-separated. Default: all the products in the package")

    op.add_option('--applications', default="",
        help="The name(s) of the application(s) to use in the test run. "+
             "Default: all the applications in the package for all devices. "+
                  "Example: 'Frank:Contacts,Messaging;Emulator:Gallery,BBC News'")

    op.add_option('--exclude', metavar='FILES', default=(),
        help="List of files to exclude from target and testrun.")

    op.add_option('--nodevice', action='store_true',
        help="Runs the modelpackage on a testadapter instead of a "+
             "(real or simulated) device. Overrides --adapter.")

    op.add_option('--nomake', action='store_true',
        help="Don't create a new target. Use the existing one.")
    op.add_option('--notestconf', action='store_true',
        help="Don't run generate-testconf. Only unpack model package and generate testconfiguration.conf file.")

    op.add_option('--norun', action='store_true',
        help="Don't run the package. Just create a runnable target.")

    op.add_option('--deviceperproduct', action='store_true',
        help="Use only one device per product")

    op.add_option('--targetdir',
        help="Device where runnable model will be generated")
    tegroup = optparse.OptionGroup(op, "arguments that are passed through to test engine")

    # argument, default value
    testengineArgs = ( ('--adapter',adapterdefault),
                       ('--adapter-args',''),
                       ('--guidance',guidancedefault),
                       ('--guidance-args',''),
                       ('--coverage',''),
                       ('--coveragereq',''),
                       ('--coveragereq-args',''),
                       ('--initmodels',''),
                       ('--config',''),
                       ('--testdata',''),
                       ('--actionpp',''),
                       ('--actionpp-args',''),
                       ('--stop-after',''),
                       ('--verify-states','0'),
                       ('--logger','fdlogger'),
                       ('--logger-args', 'targetfd:stdout') )

    for a,d in testengineArgs:
        tegroup.add_option(a,default=d,metavar="...",
                      help="testengine argument %s" %(a,),)
    op.add_option_group(tegroup)
    op.add_option('--adapter-args-model', action='store_true', default=False,
                  help="adds the created model to adapter-args")

    options,args = op.parse_args(cmdArgs)

    if options.runonport:
        options.adapter='socketserveradapter'
        options.adapter_args='port:%s' % options.runonport

    if options.nodevice:
        options.adapter='testadapter'
        options.testdata='nodata'
        options.adapter_args_model=True

    if options.exclude:
        options.exclude=[re.compile(e+'$') for e in options.exclude.split(' ')]

    if options.devices and options.deviceperproduct:
        op.error("Options 'devices' and 'deviceperproduct' are mutually exclusive")

    # Device2: App1,App2;Device2: App2,App3 -> 
    # {Device1: [App1,App2], Device2: [App2,App3]}
    apps_dict = dict([[y[0],y[1].split(",")] for y in [x.split(":",1) for x in options.applications.split(";")] if len(y) == 2])
    options.applications = apps_dict

    if options.devices:
        devices_list = [ x.split(":",1) for x in options.devices.split(" ")]
        options.devices = {}
        for d in devices_list:
            if len(d) == 1 and len(d[0].strip()) == 0:
                continue
            elif len(d) == 1:
                options.devices[d[0]] = ''
            else:
                options.devices[d[0]] = d[1]
    else:
        options.devices = {}
        


    if options.notestconf:
        options.norun = True

    if len(args) < 1:
        op.error("No modelpackage given.")
    elif len(args) > 1:
        op.error("Too many arguments.")
    if not os.path.exists(args[0]):
        op.error("File %s not found." %(args[0],))

    return args[0], options


def executableInPath(exe):
    for path in os.environ['PATH'].split(os.pathsep):
        exe_file = os.path.join(path, exe)
        if os.path.exists(exe_file) and os.access(exe_file, os.X_OK):
            return True
    return False

def isExcluded(filename,exclude):
    for e in exclude:
        if e.match(filename):
            return True
    return False

def listOfIncluded(filenames,options):
    return [f for f in filenames if not isExcluded(f,options.exclude)]

def filesInDir(dirName,fileEnding=None):
    return [f for f in os.listdir(dirName)
            if (fileEnding is None or f.endswith(fileEnding))]

def getMddFile(modelDir):
    mddFiles = filesInDir(modelDir,'.mdd')
    if len(mddFiles) != 1:
        raise RunModelPackageFailed(
            "There should be only one .mdd file. Now there are %i."
            % (len(mddFiles),) )
    return mddFiles[0]

def getMddFileWithPath(modelDir):
    return os.path.join(modelDir,getMddFile(modelDir))

def excludeDevices(dirName,tdFiles,options):
    if options.devices:
        allowedDevices = options.devices.keys()
    else:
        allowedDevices = []

    chosen = {}
    handle = None
    for tdFile in tdFiles:
        try:
            handle = open(os.path.join(dirName,tdFile),'r')
            contents = handle.readline()
        finally:
            if handle:
                handle.close()
                handle = None

        l = datareader.getDataInfo(contents)[0]
        if l in chosen and tdFile[:-3] not in allowedDevices:
            continue
        
        chosen[l]=tdFile
            
    return chosen.values()

def getTdFiles(dirName,options):
#    return listOfIncluded( filesInDir(dirName,'.td'), options )
    return excludeDevices(dirName,listOfIncluded(filesInDir(dirName,'.td'),options),options)
def getTdFilesWithPath(dirName,options):
    return [os.path.join(dirName,f) for f in getTdFiles(dirName,options)]

def getLstsFiles(dirName,options):
    return listOfIncluded( filesInDir(dirName,'.lsts'), options )
def getLstsFilesWithPath(dirName,options):
    return [os.path.join(dirName,f) for f in getLstsFiles(dirName,options)]

def getCsvFiles(dirName,options, onlyTargets = False):
    if not onlyTargets:
        return listOfIncluded( filesInDir(dirName,'.csv'), options )
    
    csvFiles = set()
    targets = getTargetDevices(dirName,options)
    for dataname,logicalname,product in targets:
        csvFiles.add("%s.csv" % product)

    return list(csvFiles)
    
def getCsvFilesWithPath(dirName,options):
    return [os.path.join(dirName,f) for f in getCsvFiles(dirName,options)]

def getActionppArgs(modelDir,targetDir,options):
    if options.actionpp_args:
        return options.actionpp_args
    mddFile = getMddFileWithPath(modelDir)
    reader = Reader(mddFile)
    targets = getTargetDevices(modelDir,options)
    actionpp_args = ""
    tdFiles = getTdFilesWithPath(targetDir,options)
    for d,l,p in targets:
        devices = reader.getValue('devices',[p]).split('\n')
        for tdFile in tdFiles:
            for device in devices:
                if tdFile.endswith(urllib.quote(device) + ".td"):
                    try:
                        handle = open(tdFile,'r')
                        contents = handle.readline()
                    finally:
                        if handle:
                            handle.close()
                            handle = None

                    log_cmp = datareader.getDataInfo(contents)[0]
                    if l == log_cmp:        
                        locales = reader.getValue('locales',[p]).split('\n')
                        actionpp_args += "file:%s:%s.csv," % (tdFile,os.path.join(targetDir,p))
                        d_quot = urllib.quote(d)
                        if d_quot in options.devices and options.devices[d_quot] not in locales and options.devices[d_quot].strip() != '':
                            raise RunModelPackageFailed(
                                "Unknown locale '%s' for device '%s'" % (options.devices[d_quot],d))
                        elif d_quot in options.devices and options.devices[d_quot].strip() != '':
                            actionpp_args += "lang:%s:%s," % (tdFile,options.devices[d_quot])
                        else:
                            actionpp_args += "lang:%s:%s," % (tdFile,locales[0])

    return actionpp_args

def getRulesFileWithPath(targetDir):
    return os.path.join(targetDir,'combined-rules.ext')

def getLstsFilesOfDevice(device,product,modelDir,options):
    mddFile = getMddFileWithPath(modelDir)
    reader = Reader(mddFile)
    concunits = reader.getValue('concurrentunits',[product]).split('\n')
    if device in options.applications:
        for selectedCu in options.applications[device]:
            if selectedCu.strip() not in concunits:
                raise RunModelPackageFailed(
                    "Error: no application named '%s' in product '%s' in device '%s'." % (selectedCu,product,device))
        concunits = options.applications[device]
    
    lstsFiles = getLstsFiles(modelDir,options)
    productLstsFiles = []
    for cu in concunits:
        cu = cu.strip()
        for lf in lstsFiles:
            if lf.startswith(cu.replace(' ','%20')):
                productLstsFiles.append(lf)
    return productLstsFiles

def getAllTargetDevices(mddFile):
    """Returns a list of (devicename,productname) tuples."""
    reader = Reader(mddFile)
    products = reader.getValue('products').split('\n')
    targets = []
    for p in products:
        devices = [d for d in reader.getValue('devices',[p]).split('\n') if d]
        targets.extend( [(d,p) for d in devices] )
    return targets

def targetDevicesAllowedByOptions(modelDir,allTargets,options):
    logicalnames = []
    selectedProducts = []

    if options.devices:
        allowedDevices = options.devices.keys()
    else:
        allowedDevices = None
    if options.products:
        allowedProducts = options.products.split() 
    else:
        allowedProducts = None

    chosen = []
    for d,p in allTargets:
        if allowedDevices and urllib.quote(d) not in allowedDevices:
            continue
        if allowedProducts and urllib.quote(p) not in allowedProducts:
            continue
        if isExcluded(d,options.exclude):
            continue

        # Options deviceperproduct and devices are mutually exclusive so we
        # don't need to check for that
        if options.deviceperproduct and p in selectedProducts:
            continue
            
        
        handle = None
        try:
            handle = open(os.path.join(modelDir,urllib.quote(d)) + ".td")
            contents = handle.readline()
        finally:
            if handle:
                handle.close()

        l = datareader.getDataInfo(contents)[0]
        if l in logicalnames:
            continue
        
        chosen.append( (d,l,p) )
        logicalnames.append(l)
        selectedProducts.append(p)
    return chosen


def unzip(basedir,ziparchive):
    def check_dir(directory):
        if not os.path.isdir(directory):
            os.makedirs(directory)
    
    zip = None
    try:
        try:
            zip = zipfile.ZipFile(ziparchive,'r')
            for item in zip.namelist():
                if not item.endswith('/'):
                    root,name = os.path.split(item)
                    directory = os.path.normpath(os.path.join(basedir,root))
                    check_dir(directory)
                    extract_item = open(os.path.join(directory, name), 'wb')
                    extract_item.write(zip.read(item))
                    extract_item.close()
                else:
                    directory = os.path.normpath(os.path.join(basedir,item))
                    check_dir(directory)
        except OSError,e:
            return False
        except IOError,e:
            return False
    finally:
        if zip != None:
            zip.close()

    return True


def getTemaMake():
    if executableInPath('tema'):
        return ['tema','do_make']
    elif executableInPath('tema.make'):
        return  ['tema.make']
    else:
        raise RunModelPackageFailed(
            "Error: no 'tema' or 'tema.make' in path.")

def getTemaTestengine():
    if executableInPath('tema'):
        return ['tema','testengine']
    elif executableInPath('tema.testengine'):
        return  ['tema.testengine']
    else:
        raise RunModelPackageFailed(
            "Error: no 'tema' or 'tema.testengine' in path.")

def createModelDirFromZip(modelPackageZip):
    modelDir = modelPackageZip[:-4]
    removeDirIfExists(modelDir)
    if not unzip(modelDir,modelPackageZip):
        raise RunModelPackageFailed("Error while unzipping.")
    return modelDir

def getTargetDevices(modelDir,options):
    mddFile = getMddFileWithPath(modelDir)
    allTargets = getAllTargetDevices(mddFile)
    if not allTargets:
        raise RunModelPackageFailed(
            "No devices defined in the model package!\n"
            "To fix: in ModelDesigner, New -> Phone\n"
            "Example MyPhone.td:\n"
            "MyPhone(id,number): [('999','040404040')]")

    targets = targetDevicesAllowedByOptions(modelDir,allTargets,options)
    if not targets:
        err = "The following options didn't match anything in the package:\n"
        if options.devices:
            err += "--devices:\n" + "\n".join(options.devices.keys()) + "\n"
        if options.products:
            err += "--products:\n" + "\n".join(options.products.split()) + "\n"
        err += "The following devices ARE defined in the package:\n" +\
            "%s" % "\n".join(["%s (product: %s)"%(d,p) for d,p in allTargets])
        raise RunModelPackageFailed(err)

    for d,l,p in targets:
        if not os.path.isdir( os.path.join(modelDir,urllib.quote(p))):
            raise RunModelPackageFailed(
                "There's no product dir '%s' in the model package."%(p,))
    return targets

def createTestConfFile(modelDir,options):
    targets = getTargetDevices(modelDir,options)
    confName = os.path.join(modelDir, 'testconfiguration.conf')

    lstsFilesByDevice = {}
    for d,l,p in targets:
        lstsFilesByDevice[d] =\
            ', '.join(getLstsFilesOfDevice(d,p,modelDir,options))

    tdFiles = getTdFiles(modelDir,options)
    csvFiles = getCsvFiles(modelDir,options,True)

    lines = []
    lines.append('[targets: type]')
    lines.extend(['%s: %s'%(t[1],urllib.quote(t[2])) for t in targets])
    lines.append('')
    lines.append('[targets: actionmachines[]]')
    lines.extend(['%s: %s' % (l,lstsFilesByDevice[d]) for d,l,p in targets])
    lines.append('')
    lines.append('[data: names[]]')
    lines.append('datatables: ' + ', '.join(tdFiles))
    lines.append('')
    lines.append('localizationtables: ' + ', '.join(csvFiles))
    lines.append('')

    confFile = file(confName,'w')
    confFile.write('\n'.join(lines))
    confFile.close()

    return confName

def generateTestConf(modelDir,confName,targetDir):
    try:
        generatetestconf.generatetestconf(modelDir,confName,targetDir)
    except Exception, e:
        raise RunModelPackageFailed(
            "Error while generating testconf:\n%s" % (e,))

def makeTarget(targetDir):
    origWorkDir = os.path.abspath(os.getcwd())
    os.chdir(targetDir)
    makeFailed=RunModelPackageFailed("Error while making the target.")
    try:
        try:
            temamake = getTemaMake()
            import subprocess
            retcode = subprocess.call(temamake)
            if retcode != 0:
                raise makeFailed
        except:
            raise makeFailed
    finally:
        os.chdir(origWorkDir)

def composeTarget(targetDir):
    composeFailed=RunModelPackageFailed("Error while making the target.")
    try:
        print targetDir
        if not composemodel.compose_model(targetDir,"compose.conf"):
            raise composeFailed
    except Exception,e:
        print e
        raise composeFailed


def getTestengineArgs(modelDir,targetDir,options):
    modelFile = getRulesFileWithPath(targetDir)
#    tdFiles = getTdFilesWithPath(targetDir,options)
    testdata = options.testdata or  ','.join(['file:%s'%f for f in getTdFilesWithPath(targetDir,options)])
    actionppArgs = getActionppArgs(modelDir,targetDir,options)
#    csvFiles = getCsvFilesWithPath(targetDir,options)

#    actionppArgs = options.actionpp_args or ",".join(['file:%s'%f for f in csvFiles])
    adapterArgs = options.adapter_args
    if options.adapter_args_model:
        if adapterArgs: adapterArgs += ','
        adapterArgs += 'model:%s'%modelFile

    teArgs = ["--model=parallellstsmodel:%s" % modelFile,
              "--testdata=%s" % testdata,
              '--coverage=%s' % options.coverage,
              "--coveragereq=%s" % options.coveragereq,
              "--coveragereq-args=%s" % options.coveragereq_args,
              "--guidance=%s" % options.guidance,
              "--guidance-args=%s" % options.guidance_args,
              "--adapter=%s" % options.adapter,
              "--adapter-args=%s" % adapterArgs,
              '--initmodels=%s' % options.initmodels,
              '--config=%s' % options.config,
              '--actionpp=%s' % options.actionpp,
              '--actionpp-args=%s' % actionppArgs,
              '--stop-after=%s' % options.stop_after,
              '--verify-states=%s' % options.verify_states,
              '--logger=%s' % options.logger,
              '--logger-args=%s' % options.logger_args]
    return teArgs

def removeDir(d):
    shutil.rmtree(d)

def removeDirIfExists(d):
    if os.path.exists(d):
        removeDir(d)

def getTargetDir(modelDir,options):
    if options.targetdir:
        return options.targetdir
    else:
        return os.path.join(modelDir, 'runnable_target')

def createNewTarget(modelDir,options):
    targetDir = getTargetDir(modelDir,options)
    removeDirIfExists(targetDir)
    confName = createTestConfFile(modelDir,options)
    if not options.notestconf:
        generateTestConf(modelDir,confName,targetDir)
        composeTarget(targetDir)
#        makeTarget(targetDir)
    return targetDir

def runTarget(targetDir,testengineArgs):
    argv_org = sys.argv[:]
    sys.argv[1:] = testengineArgs
    try:
        import tema.testengine.testengine
    except ImportError:
        testengine = getTemaTestengine()
        import subprocess
        subprocess.call(testengine + testengineArgs)

def prepareTargetDir(modelDir,options):
    if options.nomake:
        targetDir = getTargetDir(modelDir,options)
        if not os.path.exists(targetDir):
            raise RunModelPackageFailed("There is no target dir.")
    else:
        targetDir = createNewTarget(modelDir,options)
    return targetDir

def prepareModelDir(modelPackage):
    if modelPackage.endswith('.zip'):
        modelDir = createModelDirFromZip(modelPackage)
    elif os.path.isdir(modelPackage):
        modelDir = modelPackage
    else:
        raise RunModelPackageFailed(
            "Modelpackage should be a .zip file or a directory.\n")
    return modelDir

def runModelPackage(modelPackage,options):
    print "Preparing model package %s" % (modelPackage,)
    modelDir = prepareModelDir(modelPackage)
    print "The model dir is %s" % (modelDir,)
    print "Tesconfiguration file is %s/testconfiguration.conf" % (modelDir,)
    print "Preparing the target dir"
    targetDir = prepareTargetDir(modelDir,options)
    if not options.notestconf:
        print "Target ready at %s" % (targetDir,)
        print "The rules file is %s"%(getRulesFileWithPath(targetDir),)
    if not options.norun:
        print "Running the target on testengine"
        testengineArgs = getTestengineArgs(modelDir,targetDir,options)
        print "Args: %s" % (" ".join(testengineArgs),)
        runTarget(targetDir,testengineArgs)
    print "Done"

def main(cmdArgs):
    modelPackage,options = parseArgs(cmdArgs)
    try:
        runModelPackage(modelPackage,options)
    except RunModelPackageFailed, failed:
        sys.exit("-"*15+" Runmodelpackage failed! "+"-"*15+"\n" + str(failed))

if __name__=='__main__':
    main(sys.argv[1:])
