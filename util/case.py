import data, linguistics, nltk

class Case:
    def __init__(self, name):
        if name.isdigit():
            self.name = name
            self.googleURL = name
        else:
            self.name = name
            self.googleURL = data.getGoogleURL(self)
        self.string = data.getGoogleCase(self)
        trainer = nltk.tokenize.punkt.PunktSentenceTokenizer()
        trainer.train("GoogleCases.txt")
        self.tokens = trainer.tokenize(self.string)
        self.sennaMatrix = linguistics.getSennaMatrix(self)
