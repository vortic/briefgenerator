import ply.yacc as yacc

"""
http://www.cs.kuleuven.be/groups/liir/publication_files/ICAIL09-final-withBib.pdf
"""

#Terminals
tokens = (
    'N','S','RC','RS','RA','RART','VP','F'
)

t_RC = r'[tT]herefore|[tT]hus'
t_RS = r'[mM]oreover|[fF]urthermore|[aA]lso'
t_RA = r'[hH]owever|[aA]lthough'
t_RART = r'\d+\s+?Cal\.\s?[a-zA-Z0-9\.]*?\s+?\d+'
t_VP = r'[nN]ote|[rR]ecall|[sS]tate'
t_VC = r'[rR]eject|[dD]ismiss|[dD]eclare'
t_F = r'[cC]ourt|[jJ]ury|[cC]ommission'

#Nonterminals
def p_t(p):
    't:aPlus d'
    p[0] = ('General structure', p[1], p[2])

def p_a(p):
    '''a:aPlus c
        |aStar c N pPlus
        |c N S
        |aStar S RC c
        |pPlus'''
    if len(p) == 2:
        p[0] = ('Argumentative structure', p[1])
    elif len(p) == 3:
        p[0] = ('Argumentative structure', p[1], p[2])
    elif len(p) == 4:
        p[0] = ('Argumentative structure', p[1], p[2], p[3])
    elif len(p) == 5:
        p[0] = ('Argumentative structure', p[1], p[2], p[3], p[4])

def p_d(p):
    'd:RC F dHelper'
    p[0] = ('Final decision', p[1], p[2], p[3])

def p_p(p):
    '''p:pVerbP
        |pArt
        |p pSup
        |p pAg
        |S pSup
        |S pAg'''
    if len(p) == 2:
        p[0] = ('Premises', p[1])
    elif len(p) == 3:
        p[0] = ('Premises', p[1], p[2])

def p_pVerbP(p):
    'pVerbP:S VP S'
    p[0] = ('Sentence with premise verb', p[1], p[2], p[3])

def p_pArt(p):
    'pArt:S RART S'
    p[0] = ('Sentence with article reference', p[1], p[2], p[3])

def p_pSup(p):
    '''pSup:RS S
        |RS pVerbP
        |RS pArt
        |RS pSup
        |RS pAg'''
    p[0] = ('Support for an argument', p[1], p[2])

def p_pAg(p):
    '''pAg:RA S
        |RA pVerbP
        |RA pArt
        |RA pSup
        |RA pAG'''
    p[0] = ('Contrast', p[1], p[2])

def p_c(p):
    '''c:RC S
        |RC c
        |RC RC pVerbP
        |RS S
        |RS c
        |RS RC pVerbP
        |sStar VC S'''
    if len(p) == 3:
        p[0] = ('Conclusion of an argument', p[1], p[2])
    elif len(p) == 4:
        p[0] = ('Conclusion of an argument', p[1], p[2], p[3])

#Helpers
def p_empty(p):
    'empty:'
    pass

def p_aPlus(p):
    '''aPlus:a aPlus
        |a'''
    if len(p) == 2:
        p[0] = ('List of arguments', p[1])
    if len(p) == 3:
        p[0] = ('List of arguments', p[1], p[2])

def p_aStar(p):
    '''aStar:a aStar
        |empty'''
    if len(p) == 2:
        p[0] = ('List of arguments', p[1])
    if len(p) == 3:
        p[0] = ('List of arguments', p[1], p[2])

def p_pPlus(p):
    '''pPlus:p pPlus
        |p'''
    if len(p) == 2:
        p[0] = ('List of premises', p[1])
    if len(p) == 3:
        p[0] = ('List of premises', p[1], p[2])

#missing some things here - wasn't sure whether '.' was a literal or not
def p_dHelper(p):
    '''dHelper:VC S dHelper
        |VC S'''
    if len(p) == 3:
        p[0] = ('Conclusive verb', p[1], p[2])
    if len(p) == 4:
        p[0] = ('Conclusive verb', p[1], p[2], p[3])

#Error rule for syntax errors
def p_error(p):
    print "Syntax error in input!"

parser = yacc.yacc()
