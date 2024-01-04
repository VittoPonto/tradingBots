import ccxt
import pandas as pd
import sys

# Inicializa el exchange y la criptomoneda que se va a tradear
exchange = ccxt.binance({
    'apiKey': '***',
    'secret': '***',
})

par1 = 'BTC'
par2 = 'USDT'
# Símbolo del par de trading BTC/BUSD
symbol = par1 + '/' + par2

# Intervalo de tiempo en el que se calcula el RSI (por ejemplo, 1h)
interval = '1s'
# Período de tiempo para el cálculo del RSI (por ejemplo, 14)
period = 14
# CONFIGURACION
porc = 1 # porcentaje de perdida
gain_margin = 0.001


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

# Variables de seguimiento de la operación
ma7_anterior = 0
ma7_anterior2 = 0
current_price = 0.00000
buy_price = 0
stop_loss = 0
new_limit = 999999999
buyFlag = False
sellFlag = False
signal015 = False
count_01 = 0 

while True:

    # Obtiene la cantidad de BUSD y BTC disponible en la billetera
    wallet = exchange.fetch_balance()
    btc_balance = wallet[par1]['free']
    busd_balance = wallet[par2]['free']

    # Obtiene los precios de la criptomoneda
    ohlcv = exchange.fetch_ohlcv(symbol, interval, limit=7)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    ma7_actual = df['close'].rolling(window=7).mean()
    current_price = exchange.fetch_ticker(symbol)['last']
    rsi = calculate_rsi(exchange, symbol, interval, period)
    
    if ( df['close'][5] < (df['open'][1] - 0.00015*df['open'][1])):
        signal015 = True
    
    if (ma7_actual[6] > df['close'][5] and ma7_anterior > ma7_actual[6] and ma7_anterior2 > ma7_anterior and ma7_anterior2 != 0 and buyFlag == False and sellFlag == False and signal015 == True):
        buyFlag = True
        signal015 = False
        print('esperando cumplimiento de requisitos para comprar, BAJA DETECTADA')

    # Comprueba las condiciones para ejecutar una operación de compra o venta
    if (ma7_actual[6] < df['close'][5] and ma7_anterior < ma7_actual[6] and ma7_anterior2 < ma7_anterior and ma7_anterior2 != 0 and buyFlag == True): 
        print('COMPRAR')

        if busd_balance > 10:
            # Crea una orden de compra al precio actual
            amount = ((busd_balance-1) / current_price ) 
            exchange.create_market_buy_order(symbol, amount)
            print(f'Compra realizada, a {par1} = {current_price}')
            buy_price = current_price
            new_limit = buy_price+gain_margin
            buyFlag = False
            sellFlag = True
            print(f'objetivo seteado en {new_limit}')
    
    elif ( current_price < stop_loss and sellFlag == True ):       
        print('VENDER')

        if btc_balance > 10/current_price:
            # Crea una orden de venta al precio actual
            exchange.create_market_sell_order(symbol, btc_balance)
            print(f'Venta realizada, a {par1} = {current_price}')
            sellFlag = False
            buy_price = 0
            stop_loss = 0
            new_limit = 999999999
            count_01 = 0

    elif (current_price < (buy_price-(porc/100)*buy_price)):
        print('VENDER')

        if btc_balance > 10/current_price:
            # Crea una orden de venta al precio actual
            exchange.create_market_sell_order(symbol, btc_balance)
            print(f'Venta realizada, a {par1} = {current_price}  Por baja de 0.1% !!!')
            sellFlag = False
            buy_price = 0
            stop_loss = 0
            new_limit = 999999999
            count_01 = count_01+1
        
        if count_01 == 2:       # se suma las veces seguidas que se vende por baja del 0.1%
            print('Cuidado, caida de precio')
            sys.exit(0)

    else:
        print(f'NADA     RSI = {rsi}')

    if (current_price > new_limit):
        new_limit = new_limit+gain_margin
        stop_loss = current_price 
        print(f'nuevo sell price seteado en {stop_loss}')
        print(f'nuevo objetivo seteado en {new_limit}')

    ma7_anterior2 = ma7_anterior
    ma7_anterior = ma7_actual[6]
