import data, linguistics, nltk

class Case:
    def __init__(self, name, senna=True, importance=1):
        self.importance = importance
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
        if senna:
            self.sennaMatrix = linguistics.getSennaMatrix(self)
        self.SRLSentences = linguistics.getSRLSentences(self)
