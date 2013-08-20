import nltk, re, urllib2

def getHeader():
    header = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language':'en-US;q=0.8,en;q=0.6',
        'Cookie':'GSP=ID=b4effef103646c45:S=Nb2dHqpsu3vQGp-B; PREF=ID=b4effef103646c45:TM=1376994147:LM=1376994147:S=K6h-KzJXgGaRGGWt; GDSESS=ID=8e6ea0d87b9e9204:TM=1376994168:C=c:IP=98.248.250.16-:S=APGng0s7jMqLpPtO7XVOiAjLMdgkDnaCRQ',
        'Host':'scholar.google.com',
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36',
        'X-Chrome-Variations':'CNO1yQEIl7bJAQiptskBCMS2yQEIqYXKAQi3hcoB'
    }
    return header

def getGoogleURL(caseName):
    nameAndYear = caseName.split(', ')
    url = 'http://scholar.google.com/scholar?hl=en&q=' + nameAndYear[0].replace(' ', '+') + '&btnG=&as_sdt=4%2C5'
    if len(nameAndYear) > 1:
        url = url + '&as_ylo=' + nameAndYear[1]  + '&as_yhi=' + nameAndYear[1]
    print url
    header = getHeader()
    req = urllib2.Request(url, None, header)
    html = urllib2.urlopen(req).read()
    #print req.get_header('Cookie')
    urlRegex = r'scholar_case\?case=([0-9]+)'
    allLinks = []
    for result in re.finditer(urlRegex, html):
        for link in result.groups():
            allLinks.append(link)
    return allLinks[0] #Assuming the first link is the relevant one, also assuming it was cited

def getGoogleCites(caseName):
    import HTMLParser
    def fixCite(citation):
        """
        Only get one, full sentence out of the cite
        """
        citation = unicode(citation, "utf-8")
        citation = HTMLParser.HTMLParser().unescape(citation)
        sentenceRegex = r'([A-Z].*?\.)'
        finalCitation = ''
        for result in re.finditer(sentenceRegex, citation):
            for sentence in result.groups():
                if len(sentence) > len(finalCitation): #There should only be one "real" sentence
                    finalCitation = sentence
        if finalCitation == '' and citation[-1] != '.':
            return citation + '.'
        elif finalCitation == '':
            return citation
        else:
            return finalCitation
    def fixTitle(title):
        ret = title
        if 'and' in title:
            split = re.split('and', title)
            ret = split[0]
        return ret.strip()
    urlNum = getGoogleURL(caseName)
    url = 'http://scholar.google.com/scholar_case?about=' + urlNum
    header = getHeader()
    req = urllib2.Request(url, None, header)
    html = urllib2.urlopen(req).read()
    raw = nltk.clean_html(html)
    #print raw
    citeBegin = '.*?has\sbeen\scited\s+'
    #citations = '(.*?)\s-\sin.*?similar\scitations?\s+'*min(6, numCites) #No more than 9 citations are displayed
    citations = '(.*?)\s-\sin\s(.*?)\s\s'*8 #No more than 9 citations are displayed (sometimes 8)
    citeRegex = r'' + citeBegin + citations
    cites = []
    titles = []
    title = False
    for result in re.finditer(citeRegex, raw):
        for cite in result.groups():
            if title:
                titles.append(fixTitle(cite))
                title = False
            else:
                cites.append(fixCite(cite))
                title = True
    return cites, titles

def getGoogleCase(caseName):
    def removeHeading(raw):
        headingRemover = re.compile('.*?OPINION(.*)Save\strees\s-\sread', re.DOTALL)
        for result in re.finditer(headingRemover, raw):
            for case in result.groups():
                return case
        #Failure: just keep Google's stuff in there
        return raw
    urlNum = getGoogleURL(caseName)
    url = 'http://scholar.google.com/scholar_case?case=' + urlNum
    header = getHeader()
    req = urllib2.Request(url, None, header)
    html = urllib2.urlopen(req).read()
    raw = nltk.clean_html(html)
    ret = removeHeading(raw)
    if ret == None:
        print "Warning: Could not get " + caseName
    return ret

if __name__ == "__main__":
    cites, titles = getGoogleCites('224 Cal. App. 3d 885')
    """for cite, title in zip(cites, titles):
        print
        if re.match('.*\d.*', title):
            getGoogleCase(title)
        else:
            print 'failed on ' + title"""
    #print getGoogleCites('179 Cal. App. 3d 1071')
    #getGoogleCase('224 Cal. App. 3d 885')
