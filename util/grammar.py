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
    #PUT SDT HERE 

def p_a(p):
    '''a:aPlus c
        |aStar c N pPlus
        |c N S
        |aStar S RC c
        |pPlus'''
    #PUT SDT HERE 

def p_d(p):
    'd:RC F dHelper'
    #PUT SDT HERE

def p_p(p):
    '''p:pVerbP
        |pArt
        |p pSup
        |p pAg
        |S pSup
        |S pAg'''
    #PUT SDT HERE

def p_pVerbP(p):
    'pVerbP:S VP S'
    #PUT SDT HERE

def p_pArt(p):
    'pArt:S RART S'
    #PUT SDT HERE

def p_pSup(p):
    '''pSup:RS S
        |RS pVerbP
        |RS pArt
        |RS pSup
        |RS pAg'''
    #PUT SDT HERE

def p_pAg(p):
    '''pAg:RA S
        |RA pVerbP
        |RA pArt
        |RA pSup
        |RA pAG'''
    #PUT SDT HERE

def p_c(p):
    '''c:RC S
        |RC c
        |RC RC pVerbP
        |RS S
        |RS c
        |RS RC pVerbP
        |sStar VC S
    '''
    #PUT SDT HERE

#Helpers
def p_empty(p):
    'empty:'
    pass

def p_aPlus(p):
    '''aPlus:a aPlus
        |a'''
    #PUT SDT HERE

def p_aStar(p):
    '''aStar:a aStar
        |empty'''
    #PUT SDT HERE

def p_pPlus(p):
    '''pPlus:p pPlus
        |p'''
    #PUT SDT HERE

#missing some things here - wasn't sure whether '.' was a literal or not
def p_dHelper(p):
    '''dHelper:VC S dHelper
        |VC S'''
    #PUT SDT HERE

#Error rule for syntax errors
def p_error(p):
    print "Syntax error in input!"

parser = yacc.yacc()
