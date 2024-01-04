import ccxt
import time

# Inicializa el exchange y la criptomoneda que se va a tradear
exchange = ccxt.binance({
    'apiKey': '***',
    'secret': '***',
})

# Símbolo del par de trading 
par1 = 'BTC'
par2 = 'USDT'
# Símbolo del par de trading BTC/BUSD
symbol = par1 + '/' + par2

# Intervalo de tiempo en el que se calcula el RSI (por ejemplo, 1h)
interval = '1m'
# Período de tiempo para el cálculo del RSI (por ejemplo, 14)
period = 8

def calculate_rsi(exchange, symbol, interval, period):

    # Obtiene los precios de cierre de las últimas 'period' velas
    candles = exchange.fetch_ohlcv(symbol, interval)[-period:]
    closes = [candle[4] for candle in candles]
    
    # Calcula los cambios en los precios
    gains = []
    losses = []
    for i in range(1, period):
        change = closes[i] - closes[i - 1]
        if change > 0:
            gains.append(change)
        else:
            losses.append(-change)
    
    # Calcula el promedio de las ganancias y las pérdidas
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if (avg_loss == 0):
        avg_loss = 0.0001
    # Calcula el RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def trade(rsi):
    global sellFlag
    global buyFlag
    global buyFlag2

    # Obtiene el precio actual de la criptomoneda
    current_price = exchange.fetch_ticker(symbol)['last']
    # Obtiene la cantidad de BUSD y BTC disponible en la billetera
    wallet = exchange.fetch_balance()
    btc_balance = wallet[par1]['free']
    busd_balance = wallet[par2]['free']

    if rsi < 20 and buyFlag == False:
        buyFlag = True
    if rsi < 10 and busd_balance > 10 and buyFlag2 == False:
        buyFlag2 = True
    # Compro si el rsi superó los 20 pero sin haber bajado de 10
    if rsi > 21 and busd_balance > 10 and buyFlag == True and buyFlag2 == False:
        # Crea una orden de compra al precio actual
        amount = (busd_balance / current_price) -1
        exchange.create_market_buy_order(symbol, amount)
        print(f'Compra realizada, a BTC = {current_price}')
        buyFlag = False
    # Compro si el rsi superó los 10
    if rsi > 10 and busd_balance > 10 and buyFlag2 == True:
        # Crea una orden de compra al precio actual
        amount = (busd_balance / current_price) -1
        exchange.create_market_buy_order(symbol, amount)
        print(f'Compra realizada, a BTC = {current_price}')
        buyFlag2 = False

    if rsi > 65 and btc_balance > 10/current_price and sellFlag == False:
        sellFlag = True
    # Vendo si el rsi bajó de 60 o superó los 75
    if (rsi < 65 and sellFlag == True) or (rsi > 75 and sellFlag == True):
        # Crea una orden de venta al precio actual
        exchange.create_market_sell_order(symbol, btc_balance)
        print(f'Venta realizada, a BTC = {current_price}')
        sellFlag = False

sellFlag = False
buyFlag = False
buyFlag2 = False
# Calcula el RSI de BTC/BUSD en Binance
while True:
    rsi = calculate_rsi(exchange, symbol, interval, period)
    print(f'RSI de {symbol} en Binance: {rsi:.2f}')
    trade(rsi)
    #time.sleep(0.5)
 
