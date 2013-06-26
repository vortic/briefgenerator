import ply.yacc as yacc

"""
http://www.cs.kuleuven.be/groups/liir/publication_files/ICAIL09-final-withBib.pdf
"""

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

def p_t(p):
    't:aPlus d'
    #p[0] = p[1] + p[3]

def p_a(p):
    '''a:aPlus c
        |aStar c N pPlus
        |c N S
        |aStar S RC c
        |pPlus'''
    #p[0] = p[1] + p[3]

def p_d(p):
    'd:RC F dHelper'
    #p[0] = p[1] + p[3]

def p_p(p):
    '''p:pVerbP
        |pArt
        |p pSup
        |p pAg
        |S pSup
        |S pAg'''
    #p[0] = p[1] + p[3]

def p_pVerbP(p):
    'pVerbP:S VP S'
    #p[0] = p[1] + p[3]

def p_pArt(p):
    'pArt:S RART S'
    #p[0] = p[1] + p[3]

def p_pSup(p):
    '''pSup:RS S
        |RS pVerbP
        |RS pArt
        |RS pSup
        |RS pAg'''
    #p[0] = p[1] + p[3]

def p_pAg(p):
    '''pAg:RA S
        |RA pVerbP
        |RA pArt
        |RA pSup
        |RA pAG'''
    #p[0] = p[1] + p[3]

def p_c(p):
    '''c:RC S
        |RC c
        |RC RC pVerbP
        |RS S
        |RS c
        |RS RC pVerbP
        |sStar VC S
    '''
    #p[0] = p[1] + p[3]

parser = yacc.yacc()
