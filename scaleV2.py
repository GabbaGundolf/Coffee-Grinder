# scale.py
# Nach dem Flashen der Firmware auf dem ESP8266:
# import webrepl_setup
# > d fuer disable
# Dann RST; Neustart!

# Pintranslator fuer ESP8266-Boards
# LUA-Pins     D0 D1 D2 D3 D4 D5 D6 D7 D8
# ESP8266 Pins 16  5  4  0  2 14 12 13 15 
#                 SC SD
# used             I2C   

from machine import Pin,freq,SoftI2C
from time import sleep
from oled import OLED
import geometer_30 as cs
import sys
from hx711 import HX711

if sys.platform == "esp8266":
    i2c=SoftI2C(scl=Pin(5),sda=Pin(4),freq=400000)
    freq(160000000)
elif sys.platform == "esp32":
    i2c=SoftI2C(scl=Pin(22),sda=Pin(21),freq=400000)
    freq(240000000)
else:
    raise UnkownPortError()

d=OLED(i2c,128,64)
d.clearAll()

dout=Pin(14) # D5    HX711
dpclk=Pin(2) # D4    HX711
delta = 0.8
taste1=Pin(5,Pin.IN,Pin.PULL_UP)  # G5 - One shot
taste2=Pin(18,Pin.IN,Pin.PULL_UP) # G18 - Double shot
taste3=Pin(0,Pin.IN,Pin.PULL_UP) # G0 - Manual

relais1 = Pin(17, Pin.OUT)   # Für Kontakt Mühle zur Originalplatine
relais2 = Pin(16, Pin.OUT)   # Für Powerknopf Originalplatine
led4    = Pin(23, Pin.IN)    # ebenfalls wie im Original (nur Input, nicht genutzt)

singleShotWeight = 9.0
doubleShotWeight = 14.0

waitAfterGrinding = 1 #seconds
waitShowResult    = 4 #seconds

function=0

i=0

# Initialzustand (LOW)
relais1.value(0)
relais2.value(0)

def putNumber(n,xpos,ypos,show=True):
    breite=cs.number[n][0]
    for row in range(1,cs.height):
        for col in range(breite-1,-1,-1):
            c=cs.number[n][row] & 1<<col
            d.setPixel(xpos+breite+3-col,ypos+row,c,False)
    if show:
        d.show()
    return xpos+breite+2

def tara():
    d.clearAll(False)
    d.text('Tara', 46, 0, 1)
    d.show()
    hxa.tara(25)
    hxa.calFaktor(hxa.calFaktor()+delta)
    pass

def startCoffeeGrindScale(targetWeight):
    relais2.value(1)          # HIGH    
    d.text('Ziel: ' + str(targetWeight) + ' g', 0, 50, 1)
    d.show()
    pass

def home():
    d.clearAll(False)
    
    d.text('Manual', 40, 0, 1)
    
    d.text('Single', 0, 40, 1)
    d.text(str(singleShotWeight) + ' g', 0, 50, 1)

    d.text('Double', 80, 40, 1)
    d.text(str(doubleShotWeight) + ' g', 80, 50, 1)
    d.show()
    pass

def grinderOnOff():
    #Taster Hauptplatine simulieren (on/off)
    relais1.value(1)
    sleep(0.4)
    relais1.value(0)
    pass

pos=0
try:
    hxa = HX711(dout,dpclk)
    hxa.wakeUp()
    hxa.kanal(1)
    #tara()
    print("Waage gestartet")
    
    home()
    
except:
    print("HX711 initialisiert nicht")
    #for n in range(8):
    #    pos=putNumber(0,pos,0)
    d.clearAll(False)
    d.text('HX711 init failure', 0, 0, 1)
    d.show()
    
    sys.exit()
    
while 1:
    #TARA Taste
    #if taste1.value() == 0:
    #    d.clearAll(False)
    #    d.text('Tara', 0, 0, 1)
    #   d.show()
    #    pos=0
    #    #for n in range(14):
    #        #pos=putNumber(10,pos,0)
    #    hxa.tara(25)
    #    #hxb.tara(25)
    
    
    #Single Shot Taste
    if taste1.value() == 0:
        function='singleshot'
        
        grinderOnOff()
        print("Mühle (Hauptplatine) gestartet")
        
        tara()
        d.clearAll(False)
        d.text('Single shot!', 0, 0, 1)
        d.text('Please wait...', 0, 10, 1)
        shotWeight = singleShotWeight
        startCoffeeGrindScale(shotWeight)
    
    #Double Shot Taste
    elif taste2.value() == 0:
        function='doubleshot'
        
        grinderOnOff()
        print("Mühle (Hauptplatine) gestartet")
        
        tara()
        d.clearAll(False)
        d.text('Double shot!', 0, 0, 1)
        d.text('Please wait...', 0, 10, 1)
        shotWeight = doubleShotWeight
        startCoffeeGrindScale(shotWeight)
    
    #Manual Shot Taste
    elif taste3.value() == 0:
        if(function != 'manualshotcontinue'):
            function='manualshot'
            
            grinderOnOff()
            print("Mühle (Hauptplatine) gestartet")
            
            tara()
            d.clearAll(False)
            d.text('Manual shot!', 0, 0, 1)
            relais2.value(1)          # Mühle Start
        
        w=hxa.masse(10)#+hxb.masse(10)
        m="{:0.2f}".format(w)
        d.clearAll(False)
        #d.text('Ziel:' + str(shotWeight) , 0, 20, 1)
        pos=0
        m=m.replace(".",",")
        for i in range(len(m)-1):
            z=m[i]
            n=cs.chars.index(z)
            pos=putNumber(n,pos,30, False)
        z=m[len(m)-1]
        n=cs.chars.index(z)
        pos=putNumber(n,pos,30)
        
        function='manualshotcontinue'
    elif(function=='singleshot'):
        w=hxa.masse(10)#+hxb.masse(10)
        if(w>singleShotWeight):
            relais2.value(0)          # LOW
            function='singleshotend'
    elif(function=='doubleshot'):
        w=hxa.masse(10)#+hxb.masse(10)
        if(w>doubleShotWeight):
            relais2.value(0)          # LOW
            function='doubleshotend'
    elif(function=='manualshotcontinue'): #wenn manualshot, aber Knopf nicht mehr gedrückt
        relais2.value(0)          # LOW
        function='manualshotend'
    elif function == 'singleshotend' or function == 'doubleshotend' or function == 'manualshotend':
        sleep(waitAfterGrinding)
        w=hxa.masse(10)#+hxb.masse(10)
        m="{:0.2f}".format(w)
        d.clearAll(False)
        if not (function == 'manualshotend'):
            d.text('Ziel:' + str(shotWeight) , 0, 20, 1)
        pos=0
        m=m.replace(".",",")
        for i in range(len(m)-1):
            z=m[i]
            n=cs.chars.index(z)
            pos=putNumber(n,pos,30, False)
        z=m[len(m)-1]
        n=cs.chars.index(z)
        pos=putNumber(n,pos,30)
        #state=(taste1.value() == 0) #Was soll das?
        grinderOnOff()
        print("Mühle (Hauptplatine) ausgeschaltet")
        sleep(waitShowResult)
        function=0
        
    else:
        home()
        function=0
#     if state and taste1.value() == 0:
#         d.clearAll()
#         d.writeAt("Program canceled",0,0)
#         print("Programm beendet")
#         sys.exit()
    
        

