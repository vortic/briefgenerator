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
    't:aplus d'
    #p[0] = p[1] + p[3]

def p_a(p):
    '''a:aplus c
        |astar c N pplus
        |c N S
        |astar S RC c
        |pplus'''
    #p[0] = p[1] + p[3]

parser = yacc.yacc()
