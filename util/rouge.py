import summarize

def writeSystemSummaries(features, n=1):
    summaries = summarize.summarizeN(features, n=n)
    for (docsetName, feature), summary in summaries.iteritems():
        with open('rouge/systems/' + docsetName + feature + '.html', 'w') as f:
            f.write('<html>')
            f.write('<head><title>' + docsetName + '_' + feature + '</title></head>')
            f.write('<body bgcolor="white">')
            for i, sentence in enumerate(summary, start=1):
                f.write('<a name="%d">[%d]</a> <a href="#%d" id=%d>%s</a>'%(i, i, i, i, sentence))
            f.write('</body>')
            f.write('</html>')
    return summaries

def ducToModelSummary(ducFile):
    import xml.etree.ElementTree as ET
    tree = ET.parse(ducFile)
    root = tree.getroot()
    docset = root.attrib['DOCSET']
    summarizer = root.attrib['SUMMARIZER'].lower()
    selector = root.attrib['SELECTOR'].lower()
    with open('rouge/models/' + docset + selector + summarizer + '.html', 'w') as f:
        f.write('<html>')
        f.write('<head><title>' + docset + '_' + summarizer + '</title></head>')
        f.write('<body bgcolor="white">')
        for i, child in enumerate(root, start=1):
            f.write('<a name="%d">[%d]</a> <a href="#%d" id=%d>%s</a>'%(i, i, i, i, child.text))
        f.write('</body>')
        f.write('</html>')
    return root
    
def allDucToModelSummary():
    import os
    ret = []
    for (dirpath, dirnames, filenames) in os.walk('DUC/summaries/'):
        for dirname in dirnames:
            try:
                ret.append(ducToModelSummary('DUC/summaries/' + dirname + '/400e'))
            except:
                print 'No 400e summary for ' + dirname
    return ret

def writeSettings(modelSummaries, systemSummaries):
    with open('rouge/settings.xml', 'w') as f:
        f.write('<ROUGE_EVAL version="1.55">')
        f.write('<EVAL ID="TASK_1">') #generalize for more tasks
        f.write('<PEER-ROOT>rouge/systems</PEER-ROOT>')
        f.write('<MODEL-ROOT>rouge/models</MODEL-ROOT>')
        f.write('<INPUT-FORMAT TYPE="SEE"></INPUT-FORMAT>')
        f.write('<PEERS>')
        docset = None
        for i, ((docsetName, feature), summary) in enumerate(systemSummaries.iteritems(), start=1):
            f.write('<P ID="%d">%s.html</P>'%(i, docsetName + feature))
            docset = docsetName
        f.write('</PEERS>')
        f.write('<MODELS>')
        i = 1
        for root in modelSummaries:
            if root.attrib['DOCSET'] == docset:
                summarizer = root.attrib['SUMMARIZER'].lower()
                selector = root.attrib['SELECTOR'].lower()
                f.write('<M ID="%d">%s.html</M>'%(i, docset + selector + summarizer))
                i += 1
        f.write('</MODELS>')
        f.write('</EVAL>')
        f.write('</ROUGE_EVAL>')

def runRouge():
    import os
    #os.system('lib/rouge/ROUGE-1.5.5.pl -e lib/rouge/data -c 95 -2 -1 -U -r 1000 -n 4 -w 1.2 -a rouge/settings.xml > rouge/output/ROUGE-test-c95-2-1-U-r1000-n4-w1.2-a.out')
    os.system('lib/rouge/ROUGE-1.5.5.pl -e lib/rouge/data -a rouge/settings.xml > rouge/output/ROUGE-test-c95-2-1-U-r1000-n4-w1.2-a.out')

if __name__ == "__main__":
    systemSummaries = writeSystemSummaries(['unigrams'])
    modelSummaries = allDucToModelSummary()
    writeSettings(modelSummaries, systemSummaries)
    runRouge()
