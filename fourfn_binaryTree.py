#!/usr/bin/python
# -*- coding: utf-8 -*-

from pyparsing import Literal,CaselessLiteral,Word,Combine,Group,Optional,\
    ZeroOrMore,Forward,nums,alphas,alphanums,unicodeString
import math
import operator
from binarytree import Node, setup, tree, convert, pprint
#from openpyxl.compat.strings import unicode
import ChineseCharacters
import tkinter
import time
from tkinter import *
from keyword import iskeyword
exprStack = []
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
   
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
entireOpList =["&&","||","+","-","*","/","^","==","!=","<",">",">=","<=","=",]





class SpecificAnalyser:
    
    def __init__(self, reader, exprStack):   
        self.itemNameList = {}    
        self.reader = reader 
        self.exprStack = exprStack
        self.stackSymbolResult = []
        print ('length exprstack', len(exprStack))
        for i in range(0, len(exprStack)):
            self.stackSymbolResult.append ( 8 )
        self.countStackSymbol = 0
        
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

    

    
    def evaluateStack_1(self, s, line = None):
        op = s.pop()
        tempSymbolIndex = self.countStackSymbol
        self.countStackSymbol  = self.countStackSymbol + 1
        #print (op)
        if op == 'unary -':
            return -self.evaluateStack_1( s, line )
        if op in "+-*/^":
            op2 = self.evaluateStack_1( s, line )
            op1 = self.evaluateStack_1( s, line )
            result = opn[op]( op1, op2 )
            self.stackSymbolResult[tempSymbolIndex] = result
            return result
        elif op in comopnList:
            op2 = self.evaluateStack_1( s, line )
            op1 = self.evaluateStack_1( s, line )
            #print('op1 = ', op1, 'op2 = ', op2, 'operator is ', op, 'result = ',compopn[op](op1, op2 ) )
            result = compopn[op]( op1, op2 )
            self.stackSymbolResult[tempSymbolIndex] = result
            return result
        elif op in logicalopnList:
            op2 = self.evaluateStack_1( s, line )
            op1 = self.evaluateStack_1( s, line )
            result = logicalopn[op](op1, op2 )
            self.stackSymbolResult[tempSymbolIndex] = result
            return result
        
        elif op == "PI":
            return  math.pi # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in fn:
            result = self.evaluateStack_1( s, line )
            return fn[op](result)

        elif op[0].isalpha():
            #print('!op is : ' + op + ' = ', self.transformToFloat( op, line ))
            return self.transformToFloat( op, line )
        else:
            #print('@op is : ' , self.transformToFloat( op, line ))
            return self.transformToFloat( op, line )
        
    def analyzeCsv(self, resultListBox, stringPattern, pN = None):
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
            
            for i in range(0, self.countStackSymbol):
                self.stackSymbolResult[i] = 8
            self.countStackSymbol = 0
            exprStackTemp = self.exprStack[:]
            
            #print ('line content is ', line)
            if i == 0:
                i = i + 1
                resultNameLine = line
                continue
            elif i < 20:
                i = i + 1
                resultLine = line
                inconsistentItemLine = []
                result = self.evaluateStack_1(exprStackTemp, resultLine)
                print( 'final result for line ' , i, 'is = ' , result)  
                if (result == 0):
                    inconsistentLineNumber.append(i)
                resultMatrix.append(resultLine)
                inconsistentItemMatrix.append(self.stackSymbolResult) 
                #print (inconsistentItemLine)
            else:
                break
        #resultListBox.insert(END, 'Parsing compare mode: ' + stringPattern + ' OK!'  )
        return resultNameLine, resultMatrix, inconsistentItemMatrix, inconsistentLineNumber
            #print ("result" , result)




# Define your own null/sentinel value
my_null = -1

comOp = 0
not_comOp = 1
isNotKeyNode = 0
isKeyNode = 1

class MyNode(object):
    def __init__(self, data, type, result = 1, keyNodeFlag = 0, left = None, right = None, parent = None):
        self.data = data
        self.type = type
        self.result =result 
        self.l_child = left
        self.r_child = right
        self.parent = parent
        self.isKeyNode = keyNodeFlag
        
class BinaryTree(object):
    def __init__(self, strList, inconsistentItemLine):
        print (strList)
        self.NodeList = []
        index = 0
        for str in strList:
            if str in entireOpList:  
                if (inconsistentItemLine[index] == False or inconsistentItemLine[index] == 0):
                    self.NodeList.append(MyNode(str+'*', comOp, 0))
                else:
                    self.NodeList.append(MyNode(str, comOp, 1))
            else:
                self.NodeList.append(MyNode(str, not_comOp))
            
    def convert(self, NodeList):
        if not NodeList:
            return 0
        self.countNode = 0
        for Node in NodeList:
            if self.countNode == 0:
                self.root = NodeList[0]
                self.currentNode = self.root
                self.root.parent = self.root
                self.countNode = self.countNode + 1
            else:
                if self.currentNode.type == 1:
                    self.currentNode =  self.findFirstAvailableParent(self.currentNode)
                    
                Node.parent = self.currentNode
                if self.currentNode.l_child is None:
                    self.currentNode.l_child = Node
                    self.currentNode = Node
                    
                elif self.currentNode.r_child is None:
                    self.currentNode.r_child = Node
                    self.currentNode = Node
                else:
                    self.currentNode = self.findFirstAvailableParent(self.currentNode)
                    self.currentNode.r_child = Node
                    self.cuurentNode = Node
                self.countNode = self.countNode + 1
                            
    def findFirstAvailableParent(self, currentNode):
        while 1:
            if currentNode.parent.r_child == None :
                return currentNode.parent
            else:
                currentNode = currentNode.parent     
        
    #has some problems dealing with chinese characters as first node of the line
    def buildTree (self, root, inconsistentItemLine):
        if root == None:
            return [], 0, 0, 0
        line1 = []
        line2 = []
        new_root_width = gap_size = len(str(root.data))
        l_box, l_box_width, l_root_start, l_root_end = self.buildTree(root.l_child, inconsistentItemLine)
        r_box, r_box_width, r_root_start, r_root_end = self.buildTree(root.r_child, inconsistentItemLine)
        # Draw the branch connecting the new root to the left sub-box,
        # padding with white spaces where necessary
        if l_box_width > 0:
            l_root = -int(-(l_root_start + l_root_end) / 2) + 1  # ceiling
            line1.append(' ' * (l_root + 1))
            line1.append('_' * (l_box_width - l_root))
            line2.append(' ' * l_root + '/')
            line2.append(' ' * (l_box_width - l_root))
            new_root_start = l_box_width + 1
            gap_size += 1
        else:
            new_root_start = 0

        # Draw the representation of the new root
        line1.append(str(root.data))
        line2.append(' ' * new_root_width)
        # Draw the branch connecting the new root to the right sub-box,
        # padding with white spaces where necessary
        if r_box_width > 0:
            r_root = int((r_root_start + r_root_end) / 2)  # floor
            line1.append('_' * r_root)
            line1.append(' ' * (r_box_width - r_root + 1))
            line2.append(' ' * r_root + '\\')
            line2.append(' ' * (r_box_width - r_root))
            gap_size += 1
        new_root_end = new_root_start + new_root_width - 1
        
        # Combine the left and right sub-boxes with the branches drawn above
        gap = '-' * gap_size
        new_box = [''.join(line1), ''.join(line2)]
        for i in range(max(len(l_box), len(r_box))):
            l_line = l_box[i] if i < len(l_box) else '-' * l_box_width
            r_line = r_box[i] if i < len(r_box) else '*' * r_box_width
            new_box.append(l_line + gap + r_line)
            
        # Return the new box, its width and its root positions
        return new_box, len(new_box[0]), new_root_start, new_root_end

    def traverseTree(self, root, flag):    
        if root.result == 0 and root.type == comOp:
            root.isKeyNode = isKeyNode
            root.flag = flag
            flag = flag + 1
            if root.l_child.result == 0 :
                self.traverseTree(root.l_child, flag)
                
            if root.r_child.result == 0 :
                self.traverseTree(root.r_child, flag)
                
        elif root.result ==0 and root.type == not_comOp:
            root.isKeyNode = isKeyNode
            root.flag = flag
            return
                
    def printTree(self, inconsistentItemMatrix):
        '''
        new_box = self.buildTree(self.root)[0]
        for line in new_box:
            flag = 0
            for character in line:
                if character =='':
                    continue
                elif character in ChineseCharacters.unicodeList:
                    print('',line)
                    flag =  1
                    break
            if flag == 0:
                print (line)
        print()
        '''
        #print(new_box[0])
        print('\n' + '\n'.join(self.buildTree(self.root, inconsistentItemMatrix[0])[0]))          
          
    def printTree_Simple(self): 
        for node in self.NodeList:
            l = ''
            r = ''
            if node.l_child == None:
                l = 'None'
            else:
                l = node.l_child.data
            if node.r_child == None:
                r = 'None'
            else:
                r = node.r_child.data
                
            if node.parent == node:
                parent = node.parent.data + '(self)'
            else:
                parent = node.parent.data
            try:
                print (node.data, '    ' ,parent, '    ', l, '    ', r)
            except AttributeError:
                print('Error    ', node.data)
            print ()
            
if __name__ == "__main__":
    
    def test( s, expVal ):
        global  exprStack
        exprStack = []
        resultListBox= []
        results = BNF().parseString( s )
        #print("results  =  ")
        #print(results)
        print("end")
        exprStackTemp = exprStack[:]
        exprStackTemp.reverse()
        reader = [['a1','a2','a3','a4'],[1,'123',3,4],[5,6,7,8],[9,10,11,12]]
        sa = SpecificAnalyser(reader, exprStack)
        resultNameLine, resultMatrix, inconsistentItemMatrix, inconsistentLineNumber = sa.analyzeCsv(resultListBox, s)
        print (exprStackTemp)
        print (sa.stackSymbolResult)
        
        bt = BinaryTree(exprStackTemp, inconsistentItemMatrix[0])
        bt.convert(bt.NodeList)
        bt.printTree(inconsistentItemMatrix)
        #bt.printTree_Simple()
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
    test("(a1 == 1 || a1 >= 5  && ((a2 ) = 123  )  && (a3 <= 3) ) && (6)", 2)
    #test(" ( a2 == 我爱你E )  && (6)", 2)
    #a = float('4294967.0')
    #print(operator.eq(a, 4294967))
