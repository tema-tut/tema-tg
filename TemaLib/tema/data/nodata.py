
class TestData:

    def __init__(self):
        self.log("Initialized without data prosessing.")
        
    
    def setParameter(self,name,value):
        pass

    def prepareForRun(self):
        pass

    def processAction(self,actionstring):
        return actionstring

    def log(*a): pass
