#!/usr/bin/env python3
# Project Tutorial Url:http://www.markwheeler.com
#  

import smbus
import time
import os
import glob
import subprocess
from datetime import datetime
import threading
from multiprocessing import Process
import psutil
from grove.display.jhd1802 import JHD1802
from grove.factory import Factory
from time import sleep

#lcd = JHD1802()

#import mpd
#from socket import error as SocketError
 
#client = mpd.MPDClient()


# Define some device parameters
I2C_ADDR  = 0x3e # I2C device address, if any error, change this address to 0x3f
LCD_WIDTH = 16   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#Open I2C interface
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)

def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = the data
  # mode = 1 for data
  #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

  # High bits
  bus.write_byte(I2C_ADDR, bits_high)
  lcd_toggle_enable(bits_high)

  # Low bits
  bus.write_byte(I2C_ADDR, bits_low)
  lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
  # Toggle enable
  time.sleep(E_DELAY)
  bus.write_byte(I2C_ADDR, (bits | ENABLE))
  time.sleep(E_PULSE)
  bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
  time.sleep(E_DELAY)

#def lcd.write(message,line,style):
  # Send string to display
  # style=1 Left justified
  # style=2 Centred
  # style=3 Right justified

#  if style==1:
#    message = message.ljust(LCD_WIDTH," ")
#  elif style==2:
#    message = message.center(LCD_WIDTH," ")
#  elif style==3:
#    message = message.rjust(LCD_WIDTH," ")

#  lcd_byte(line, LCD_CMD)

#  for i in range(LCD_WIDTH):
#    lcd_byte(ord(message[i]),LCD_CHR)

# Is MPD playing a song?
def mpc_status():
    playing = (os.popen('mpc status | grep playing')).readline()
    if playing=="":
        return(0)
    elif playing != "":
	    return(1)

		
# Stuff to Display
def measure_temp():
    temp = os.popen('vcgencmd measure_temp').readline()
    return(temp.replace("temp=","").replace("'C\n",""))

def ip_address():
    ip = os.popen('hostname -I').readline()
    return(ip.strip())

def cpu_load():
    CPU_Pct=str(round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }' ''').readline()),2))
    return(str(CPU_Pct))

def ram_used():
    mem_used = (psutil.virtual_memory().used  / (1024.0 ** 2))
    return(str(round(mem_used,2)))

def current_song():
    song = os.popen('mpc -f %title%').readline()
    return(song.strip())

def current_artist():
    title = os.popen('mpc -f %artist%').readline()
    return(title.strip())

def current_time():
    stime = os.popen('mpc -f %time%').readline()
    return(stime.strip())

def current_album():
    album = os.popen('mpc -f %album%').readline()
    return(album.strip())

def long_album():
    str_album = " " * 20
    long_album = str_album + current_album()
    for i in range (0, len(long_album)):
        lcd_text = long_album[i:(i+20)]
        lcd.write(lcd_text,LCD_LINE_2,1)
        time.sleep(0.4)
        lcd.write(str_album,LCD_LINE_2,1)
        continue

def radio_song():
    sstring = os.popen('mpc -f %title%').readline()
    astring = os.popen('mpc -f %title%').readline()
    song = sstring.split('-')[1]
    artist = astring.split('-')[0]
    lcd.write(artist.strip(),LCD_LINE_1,2)
    lcd.write(song.strip(),LCD_LINE_2,2)
	
def long_song():
    str_song = " " * 20
    long_song = str_song + current_song()
    for i in range (0, len(long_song)):
        lcd_text = long_song[i:(i+20)]
        lcd.write(lcd_text,LCD_LINE_1,1)
        time.sleep(0.05)
        lcd.write(str_song,LCD_LINE_1,1)
        lcd.write(song_elapsed()+"/"+current_time(),LCD_LINE_4,3)

def scroll_title():
    str_title = " " * 20
    str_album = " " * 20
    long_title = str_title + current_song()
    long_album = str_album + current_album()
    while True:
        for i in range (0, 32):
            lcd_text1 = long_title[i:(i+20)]
            lcd_text2 = long_album[i:(i+20)]
            lcd.write(lcd_text1,LCD_LINE_3,1)
            lcd.write(lcd_text2,LCD_LINE_2,1)
            time.sleep(0.05)
            lcd.write(str_title,LCD_LINE_3,1)
            lcd.write(str_album,LCD_LINE_2,1)
            continue

# MPD connection times out
#def song_elapsed():
#    elapsed = client.status()['elapsed']
#    m, s = divmod(int(float(elapsed)), 60)
#    h, m = divmod(m, 60)
#    elapsed_min = ("%02d:%02d" % (m, s))
#    return(elapsed_min)

def song_elapsed():
    elapsed = os.popen('mpc status | awk \'NR==2 { split($3, a, "/"); print a[1]}\'').readline()
    return(elapsed.strip())


  # Main program block
def main():
    lcd = JHD1802()

  # Initialise display
    lcd_init()

# Display Method
while True:
# Call MPD Display if Running
#    client.connect("localhost", 6600)
#    if client.status()['state'] == "play":
#        lcd.write("MPD is PLAYING",LCD_LINE_2,1)
#        client.disconnect()
#        os.system('/home/pi/scripts/mpd_display.py')	
#    else:
#        client.disconnect()  

# Call MPD Display if Running
    if mpc_status() == 0:
        #os.system('/home/pi/scripts/mpd_display.py')
        # Display Data
        lcd.write(datetime.now().strftime('%m/%d/%Y %H:%M'),LCD_LINE_1,2)
        lcd.write(ip_address(),LCD_LINE_2,2)
        lcd.write("CPU: "+measure_temp()+"c "+cpu_load()+"%",LCD_LINE_3,2)
#       lcd.write(" ",LCD_LINE_3,1)
        lcd.write("RAM FREE: "+ram_used()+"Mgb",LCD_LINE_4,2)
        time.sleep(1)
    elif mpc_status() == 1:
        if (len(current_artist()) == 0):
            sstring = os.popen('mpc -f %title%').readline()
            astring = os.popen('mpc -f %title%').readline()
            song = sstring.split('-')[1]
            artist = astring.split('-')[0]
            lcd.write(artist.strip(),LCD_LINE_1,2)
            lcd.write(song.strip(),LCD_LINE_2,2)
            lcd.write(song_elapsed()+" / Stream Time",LCD_LINE_4,3)
        else:
            lcd.write(current_artist(),LCD_LINE_1,1)
            lcd.write(current_album(),LCD_LINE_2,1)
            lcd.write(current_song(),LCD_LINE_3,1)
            lcd.write(song_elapsed()+"/"+current_time(),LCD_LINE_4,3)

        time.sleep(0.1)
       

if __name__ == '__main__':

  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    lcd_byte(0x01, LCD_CMD)
