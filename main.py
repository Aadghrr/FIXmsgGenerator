from random import random,choice,gauss
import sys,string,datetime

def now():
    return datetime.datetime.now().strftime("%y-%m-%dT:%H:%M:%S")

def getPrice(side,sym):
    book = buybook if side == 's' else sellbook
    px = book.get(sym,[])
    px = choice(range(1,11))*10 if len(px) == 0 else px[0].px
    return round(gauss(px,0.5),2)

class Trade():
    def __init__(self,*args):
        self.traderId, self.sym, self.px,self.vol,self.side,self.ordType = args
    def __repr__(self):
        return 'traderId: '+str(self.traderId)+' sym: '+str(self.sym)+' px: '+str(self.px)+' vol: '+str(self.vol)+' side: '+str(self.side)+' ordType: '+str(self.ordType)

class Trader():
    def __init__(self, id):
        self.id =id
        self.name = 'trd'
        self.bank = 'bnk' +''.join([choice(string.ascii_lowercase+string.digits) for _ in range(32)])
        self.portfolio = {x:round(200*(1+random())) for x in syms}
        self.cash = 1000
        self.numTrades = 0
    def createMarketOrder(self):
        sym = choice(syms)
        side = choice('bs')
        trade = makeTrade(self.id,sym,0,10*round(10*(1+random())),side,'market')
        match(trade)
        logFIX(trade,'newOrderSingle')
    def createLimitOrder(self):
        sym = choice(syms)
        side = choice('bs')
        px = getPrice(side,sym)
        trade = makeTrade(self.id,sym,px,10*round(10*(1+random())),side,'limit')
        match(trade)
        logFIX(trade,'newOrderSingle')
    def executeSell(self,sym,trade):
        self.cash = round(self.cash + trade.px*trade.vol,2)
        self.portfolio[sym] = self.portfolio[sym] - trade.vol
    def executeBuy(self,sym,trade):
        self.portfolio[sym] = self.portfolio[sym] + trade.vol
        self.cash = round(self.cash - trade.px*trade.vol,2)

listOfTraders = {}
def createTraders(n):
    for _ in range(n):
        id = 'usr'+''.join([choice(string.ascii_lowercase+string.digits) for _ in range(32)])
        listOfTraders.update({id:Trader(id)})
    #Creating a trader to represent the market maker
    listOfTraders.update({'mm':Trader('mm')})

def makeTrade(traderId=None, sym=None, px=None, vol=None, side=None, ordType=None):
    return Trade(traderId,sym,px,vol,side,ordType)

buybook = {}
sellbook = {}
syms = ['CRM','GOOG','MSFT','TSLA']
for sym in syms:
    buybook.update({sym:[]})
    sellbook.update({sym:[]})

def createOrder(trade):
    s = 'Ask' if trade.side =='s' else 'Bid'
    book = sellbook if trade.side == 's' else buybook
    #print('Created order',trade.side,':',trade)
    logFIX(trade,'executionReportNew')
    book[trade.sym].append(trade)
    book[trade.sym].sort(key=lambda x:x.px)

def executionCallback(sym,side,trade):
    traderId = trade.traderId
    if side == 's':
        listOfTraders[traderId].executeSell(sym,trade)
    else:
        listOfTraders[traderId].executeBuy(sym,trade)

def marketOrder(book, trade):
    nearSide = 'b' if book == buybook else 's'
    farSide = 'b' if nearSide == 's' else 's'
    sym = trade.sym
    while trade.vol > 0:
        if len(book[sym])==0:
            print(trade.sym,' market order failed. No liquidity in the book', trade)
            return
        else:
            v = trade.vol - book[sym][0].vol
            if v < 0:
                print('Executed trade: ',trade, ' against ',book[sym][0])
                executionCallback(sym,farSide,makeTrade(traderId=book[sym][0].traderId,sym=sym,px=book[sym][0].px,vol=trade.vol,side=farSide))
                logFIX(makeTrade(traderId=book[sym][0].traderId,sym=sym,px=book[sym][0].px,vol=trade.vol,side=farSide),'executionReportPartiallyFilled')
                executionCallback(sym,trade.side,trade)
                logFIX(trade,'executionReportFilled')
                book[sym][0].vol = abs(v)
                return
            elif v ==0:
                print('Executed trade: ',trade, ' against ',book[sym][0])
                executionCallback(sym,farSide,book[sym][0])
                logFIX(book[sym][0],'executionReportFilled')
                executionCallback(sym,trade.side,trade)
                logFIX(trade,'executionReportFilled')
                book[sym].pop(0)
                return
            elif v> 0:
                print('Executed Partial trade: ',trade, ' against ',book[sym][0])
                trade.vol = book[sym][0].vol
                executionCallback(sym,farSide,book[sym][0])
                logFIX(book[sym][0],'executionReportFilled')
                executionCallback(sym,trade.side,trade)
                logFIX(trade,'executionReportPartiallyFilled')

                trade.vol = v
                book[sym].pop(0)
                continue

def limitOrder(book, trade):
    nearSide = trade.side
    farSide = 'b' if nearSide == 's' else 's'
    #s = trade.side
    sym = trade.sym
    while trade.vol > 0:
        if len(book[sym])==0:
            createOrder(trade)
            return
        elif nearSide == 'b':
            v = trade.vol - book[sym][0].vol
            if trade.px >= book[sym][0].px and v < 0:
                print('Executed buy: ',trade, 'against ',book[sym][0])
                executionCallback(sym,farSide,makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=trade.vol,side=farSide))
                logFIX(makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=trade.vol,side=farSide),'executionReportPartiallyFilled')
                executionCallback(sym,nearSide,trade)
                logFIX(trade,'executionReportFilled')
                book[sym][0].vol = abs(v)
                return 
            elif trade.px >= book[sym][0].px and v == 0:
                print('Executed buy: ',trade, 'against ',book[sym][0])
                executionCallback(sym,farSide,makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=trade.vol,side=farSide))
                logFIX(makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=trade.vol,side=farSide),'executionReportFilled')
                executionCallback(sym,nearSide,trade)
                logFIX(book[sym][0],'executionReportFilled')
                book[sym].pop(0)
                return 
            elif trade.px >= book[sym][0].px and v > 0:
                print('Executed partial buy: ',trade, 'against ',book[sym][0])
                executionCallback(sym,farSide,makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=book[sym][0].vol,side=farSide))
                logFIX(makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=book[sym][0].vol,side=farSide),'executionReportFilled')
                trade.vol = v
                executionCallback(sym,nearSide,trade)
                logFIX(trade,'executionReportPartiallyFilled')
                book[sym].pop(0)
                continue
            else:
                createOrder(trade)
                return
        elif nearSide == 's':
            v = trade.vol - book[sym][0].vol
            if trade.px <= book[sym][0].px and v < 0:
                print('Executed Sell: ',trade, ' against ',book[sym][0])
                executionCallback(sym,farSide,makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=trade.vol,side=farSide))
                logFIX(makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=trade.vol,side=farSide),'executionReportPartiallyFilled')
                executionCallback(sym,nearSide,trade)
                logFIX(trade,'executionReportFilled')
                book[sym][0].vol = abs(v)
                return
            elif trade.px <= book[sym][0].px and v == 0:
                print('Executed Sell: ',trade, ' against ',book[sym][0])
                executionCallback(sym,farSide,makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=trade.vol,side=farSide))
                logFIX(makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=trade.vol,side=farSide),'executionReportFilled')
                executionCallback(sym,nearSide,trade)
                logFIX(trade,'executionReportFilled')
                book[sym].pop(0)
                return
            elif trade.px <= book[sym][0].px and v > 0:
                print('Executed Partial Sell: ',trade, ' against ',book[sym][0])
                executionCallback(sym,farSide,makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=book[sym][0].vol,side=farSide))
                logFIX(makeTrade(traderId=book[sym][0].traderId,sym=sym,px=trade.px,vol=book[sym][0].vol,side=farSide),'executionReportFilled')
                trade.vol = v
                executionCallback(sym,nearSide,trade)
                logFIX(trade,'executionReportPartiallyFilled')
                book[sym].pop(0)
                continue
            else:
                createOrder(trade)
                return

def offerQuotes(n):
    #Making the market
    for sym in syms:
        for _ in range(n):
            px = getPrice('s',sym) + getPrice('b',sym)
            ps = px/2
            b = makeTrade('mm',sym,px,200,'b','limit')
            s = makeTrade('mm',sym,px,200,'s','limit')
            createOrder(b)
            createOrder(s)

def match(trade):
    #print(trade)
    book = sellbook if trade.side == 'b' else buybook
    if trade.ordType == 'limit':
        limitOrder(book,trade)
    elif trade.ordType == 'market':
        marketOrder(book,trade)

def generateTrades(n):
    for c in range(n):
        #print(c,'. ',sep='',end='')
        t = listOfTraders[choice(list(listOfTraders.keys()))]
        if choice(range(4)) == 0:
            t.createMarketOrder()
        else:
            t.createLimitOrder()

def showSpreads():
    print('sym bidVol bid ask askVol')
    print(50*'-')
    for sym in syms:
        print(sym,buybook[sym].__len__(),buybook[sym][0].px,sellbook[sym][0].px,sellbook[sym].__len__(),sep='\t')

def showTraderPerf():
    print('TraderId Cash Portfolio')
    for t in listOfTraders:
        print(t,listOfTraders[t].cash,listOfTraders[t].portfolio)

def printFIX(trade, msgType):
    #FIX 4.4
    msg = {
        'newOrderSingle' : f"11=ClOrdID|55={trade.sym}|54={1 if trade.side == 'b' else 2}|60={now()}|38={trade.vol}|40={1 if trade.ordType == 'Market' else 2}|",
        'executionReportNew' : f"37=OrderID|17=ExecID|150=0|39=0|55={trade.sym}|54={1 if trade.side == 'b' else 2}|151=LEAVESQTY|14=CUMQTY|6=AvgPX|60={now()}|",
        'executionReportPartiallyFilled' : f"37=OrderID|17=ExecID|150=F|39=F|55={trade.sym}|54={1 if trade.side == 'b' else 2}|151=LEAVESQTY|14=CUMQTY|6=AvgPX|60={now()}|",
        'executionReportFilled' : f"37=OrderID|17=ExecID|150=F|39=F|55={trade.sym}|54={1 if trade.side == 'b' else 2}|151=LEAVESQTY|14=CUMQTY|6=AvgPX|60={now()}|"
        }
    msg = msg.get(msgType)
    header=f"8=FIX4.4|9={sys.getsizeof(msg)}|35={msgType}|49=SENDER|56=RECEIVER|34=MsgSeqNum|52=SendTime|"
    footer=f"10={sum(msg.encode())}"
    return header+msg+footer

def printOrder(trade):
    return f"ClOrdID,{trade.sym},{1 if trade.side == 'b' else 2},{now()},{trade.vol},{1 if trade.ordType == 'Market' else 2}"

def logFIX(trade, msgType):
    with open('fix.log','a') as f:
        f.write(printFIX(trade,msgType)+'\n')
        f.close()
    if msgType == 'newOrderSingle':
        with open('order.log','a') as f:
            f.write(printOrder(trade)+'\n')
            f.close()

with open('order.log','w') as f:
    f.write("CLOrdID,sym,side,time,vol,orderType"+'\n')
    f.close()
createTraders(10)
offerQuotes(len(syms)*100)
generateTrades(100)
