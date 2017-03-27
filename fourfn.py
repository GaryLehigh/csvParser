#!/usr/bin/python
# -*- coding: utf-8 -*-

from pyparsing import Literal,CaselessLiteral,Word,Combine,Group,Optional,\
    ZeroOrMore,Forward,nums,alphas,alphanums,unicodeString
import math
import operator
#from openpyxl.compat.strings import unicode
import ChineseCharacters
import tkinter
import time
from tkinter import *
exprStack = []

def pushFirst( strg, loc, toks ):
    exprStack.append( toks[0] )
def pushUMinus( strg, loc, toks ):
    if toks and toks[0]=='-': 
        exprStack.append( 'unary -' )
        #~ exprStack.append( '-1' )
        #~ exprStack.append( '*' )

def andand (a, b):
    if a!=0 and b!=0:
        return 1
    else:
        return 0
def oror(a, b):
    if a!=0 or b!=0:
        return 1
    else:
        return 0
    

    
bnf = None
def BNF():
    """
    expop   :: '^'
    multop  :: '*' | '/'
    addop   :: '+' | '-'
    integer :: ['+' | '-'] '0'..'9'+
    atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
    factor  :: atom [ expop factor ]*
    term    :: factor [ multop factor ]*
    expr    :: term [ addop term ]*
    equation:: expr [equality expr]*
    logic :: equation [logicalop equation]*
    """
    global bnf
    if not bnf:
        point = Literal( "." )
        e     = CaselessLiteral( "E" )
        fnumber = Combine( Word( "+-"+nums, nums ) + 
                           Optional( point + Optional( Word( nums ) ) ) +
                           Optional( e + Word( "+-"+nums, nums ) ) )
        #columnName = Word(alphanums)
            
       
        ident = Word(alphas+ChineseCharacters.unicodeList + nums, ChineseCharacters.unicodeList+alphas+nums+"_$[]")
        
        
        
        plus  = Literal( "+" )
        minus = Literal( "-" )
        mult  = Literal( "*" )
        div   = Literal( "/" )
        andand = Literal("&&")
        oror = Literal("||")
        is_a1 = Literal("==")
        is_a2 = Literal("=")
        is_a = is_a1 | is_a2
        less_than = Literal("<")
        bigger_than = Literal(">")
        bigger_or_equal = Literal(">=")
        less_or_equal = Literal("<=")
        is_not_a = Literal("!=")
        
        lpar  = Literal( "(" ).suppress()
        rpar  = Literal( ")" ).suppress()
        addop  = plus | minus
        multop = mult | div
        compop = is_a | is_not_a | less_than | bigger_than 
        compop2 = bigger_or_equal | less_or_equal
        logical = andand | oror
        expop = Literal( "^" )
        pi    = CaselessLiteral( "PI" )
        
        logic = Forward()
        atom = (Optional("-") + ( ident  | e | fnumber | pi + lpar + logic + rpar).setParseAction( pushFirst ) | ( lpar + logic.suppress() + rpar )).setParseAction(pushUMinus) 
         
        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-righ
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + ZeroOrMore( ( expop + factor ).setParseAction( pushFirst ) )
        
        term = factor + ZeroOrMore( ( multop + factor ).setParseAction( pushFirst ) )
        expr = term + ZeroOrMore( ( addop + term ).setParseAction( pushFirst ) )
        equation = expr + ZeroOrMore( ( compop + expr ).setParseAction(pushFirst) )
        equation2 = equation + ZeroOrMore( ( compop2 + expr ).setParseAction(pushFirst) )
        logic << equation2 + ZeroOrMore( ( logical + equation2 ).setParseAction(pushFirst) )
        bnf = logic
    return bnf

# map operator symbols to corresponding arithmetic operations
epsilon = 1e-12
opn = { "+" : operator.add,
        "-" : operator.sub,
        "*" : operator.mul,
        "/" : operator.truediv,
        "^" : operator.pow}
fn  = { "sin" : math.sin,
        "cos" : math.cos,
        "tan" : math.tan,
        "abs" : abs,
        "trunc" : lambda a: int(a),
        "round" : round}
compopn = {
        "==" : operator.eq,
        "="  : operator.eq,
        "!=" : operator.ne,
        ">"  : operator.gt,
        "<"  : operator.lt,
        ">=" : operator.ge,
        "<=" : operator.le
    }
comopnList = ["==", "!=", "<", ">", ">=", "<=", "="]

logicalopn = {
        "&&" :  andand,
        "||" : oror
        }
logicalopnList = ["&&", "||"]





class SpecificAnalyser:
    
    def __init__(self, reader, exprStack):   
        self.itemNameList = {}    
        self.reader = reader 
        self.exprStack = exprStack
        
    def transformToFloat(self,s, line):
        try:
            #print(s , 'is float ', float(s))
            return float(s)
        except ValueError:
            try:
                try:
                    #print (line)
                    #print (self.itemNameList)
                    return float(line[self.itemNameList[s]])
                except ValueError:
                    return line[self.itemNameList[s]]
            except KeyError:
                #print(s , 'is string ', str(s))
                return str(s)

    
    def evaluateStack(self, s, inconsistentItemLine, line = None):
        op = s.pop()
        #print (op)
        if op == 'unary -':
            return -self.evaluateStack( s, inconsistentItemLine, line )
        if op in "+-*/^":
            op2 = self.evaluateStack( s, inconsistentItemLine, line )
            op1 = self.evaluateStack( s, inconsistentItemLine, line )
            return opn[op]( op1, op2 )
        elif op in comopnList:
            op2 = self.evaluateStack( s, inconsistentItemLine, line )
            op1 = self.evaluateStack( s, inconsistentItemLine, line )
            #print('op1 = ', op1, 'op2 = ', op2, 'operator is ', op, 'result = ',compopn[op](op1, op2 ) )
            return compopn[op](op1, op2 )
        elif op in logicalopnList:
            op2 = self.evaluateStack( s, inconsistentItemLine, line )
            op1 = self.evaluateStack( s, inconsistentItemLine, line )
            return logicalopn[op](op1, op2 )
        elif op == "PI":
            return math.pi # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in fn:
            return fn[op]( self.evaluateStack( s, inconsistentItemLine, line ) )
        elif op[0].isalpha():
            #print('!op is : ' + op + ' = ', self.transformToFloat( op, line ))
            return self.transformToFloat( op, line )
        else:
            #print('@op is : ' , self.transformToFloat( op, line ))
            return self.transformToFloat( op, line )
    
    def analyzeCsv(self, resultListBox, pN = None):
        i = 0
        resultNameLine = []
        resultMatrix = []
        inconsistentItemMatrix = []
        #The first line is Column Name
        rowCount = len(self.reader) 
        #print ('rowCount ' , rowCount)
        columnCount = len(self.reader[0])
        #print ("columnCount " , columnCount)
        for j in range(columnCount):
            self.itemNameList[self.reader[0][j]] = j
        #print (itemNameList)
        inconsistentLineNumber = []
        for line in self.reader:
            exprStackTemp = self.exprStack[:]
            resultListBox.insert(END, '' )
            #print ('line content is ', line)
            if i == 0:
                i = i + 1
                resultNameLine = line
                continue
            elif i < 20:
                i = i + 1
                resultLine = line
                inconsistentItemLine = []
                result = self.evaluateStack(exprStackTemp, inconsistentItemLine, resultLine)
                print( 'final result for line ' , i, 'is = ' , result)  
                if (result == 0):
                    inconsistentLineNumber.append(i)
                resultMatrix.append(resultLine)
                inconsistentItemMatrix.append(inconsistentItemLine) 
            else:
                break
        return resultNameLine, resultMatrix, inconsistentItemMatrix, inconsistentLineNumber
            #print ("result" , result)
            
if __name__ == "__main__":
    
    def test( s, expVal ):
        global  exprStack
        exprStack = []
        results = BNF().parseString( s )
        #print("results  =  ")
        #print(results)
        print("end")
        print(exprStack)
        reader = [['a1','a2','a3','a4'],[1,'我爱你E',3,4],[5,6,7,8],[9,10,11,12]]
        sa = SpecificAnalyser(reader, exprStack)
        sa.analyzeCsv()
        
        '''
        val = evaluateStack(exprStack)
        
        if val == expVal:
            print (s, "=", val, results, "=>", exprStack)
        else:
            print (s+"!!!!!", val, "!=", expVal, results, "=>", exprStack)
    '''    
        
    #test( "9 + 3 / 11", 9 + 3.0 / 11 )        
    #test( "(0 == ErrorCode)   &&     (PrbBitmap[1] >= (0xf0000000 - 1) || 0 == PrbBitmap[1] ) &&    (TB0_AckState < 4) &&    (TB1_AckState < 4) " , 2 )
    #test( "(0 == ErrorCode)   &&     (PrbBitmap[1] > (0xf0000000 - 1) || 0 == PrbBitmap[1] ) &&    (TB0_AckState < 4) &&    (TB1_AckState < 4) " , 2 )
    test("(a1 == 1 || a1 == 5  && ((a2 ) = 我爱你E )  && (a3 <= 3) )+ (5)", 2)
    #a = float('4294967.0')
    #print(operator.eq(a, 4294967))
