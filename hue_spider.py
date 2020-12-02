import sys
import sqlite3
from phue import Bridge
import time

# Get credentials for my HueBridge
# For security reasons not in this project
# functions in hidden.py just returns IP-adress and the API-user key
# see Hue Developpers site for info on generating a API-user key
import hidden
myIP = hidden.MyBridgeIP()
myUserID = hidden.MyBridgeUserID()

#Connect to database
conn = sqlite3.connect('.\database\HueSystem.sqlite')
cur = conn.cursor()

#Check for paramater "refresh". If set, start with fresh tables
if len(sys.argv) > 1:
    if sys.argv[1] == 'refresh':
        cur.execute('DROP TABLE IF EXISTS lights')
        cur.execute('DROP TABLE IF EXISTS sensors')
        cur.execute('DROP TABLE IF EXISTS sensorstate')
        cur.execute('DROP TABLE IF EXISTS sensorconfig')
        cur.execute('DROP TABLE IF EXISTS group')
        cur.execute('DROP TABLE IF EXISTS groupmembers')

#Create tables
cur.executescript('''
    CREATE TABLE IF NOT EXISTS lights \
    (id INTEGER PRIMARY KEY AUTOINCREMENT, light_id INTEGER, name TEXT UNIQUE, ltype TEXT, reachable BOOLEAN, onstate BOOLEAN, \
    alert TEXT, brightness INTEGER, colormode TEXT, colortemp INTEGER, \
    hue INTEGER, sat INTEGER, xyValue TEXT, effect TEXT);

    CREATE TABLE IF NOT EXISTS sensors \
    (id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id INTEGER, name TEXT UNIQUE, modelid TEXT, swversion TEXT, stype TEXT, \
    manufacturername TEXT);

    CREATE TABLE IF NOT EXISTS sensorstate \
    (id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id INTEGER, stateitem TEXT, statevalue TEXT, UNIQUE(sensor_id, stateitem));

    CREATE TABLE IF NOT EXISTS sensorconfig \
    (id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id INTEGER, configitem TEXT, configvalue TEXT, UNIQUE(sensor_id, configitem));

    CREATE TABLE IF NOT EXISTS groups \
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE);

    CREATE TABLE IF NOT EXISTS groupmembers \
    (group_id INTEGER, light_id INTEGER, UNIQUE(group_id, light_id));

    ''')

#Connect to the Hue Bridge, using "hidden" credentials
b = Bridge(myIP, myUserID)

#Retreve Lights
print('Retrieving lights...')
lights = b.get_light_objects()

for light in lights:
    #General properties
    lid = light.light_id
    lname = light.name
    ltype = light.type
    lreachable = light.reachable
    lon = light.on
    lalert = light.alert
    lbrightness = light.brightness

    #Type depending properties
    try:
        lcolormode = light.colormode
    except:
        lcolormode = ''
    try:
        lhue = light.Hue
    except:
        lhue = 0
    try:
        lsaturation = light.saturation
    except:
        lsaturation = 0
    try:
        lxy = light.xy
    except:
        lxy = ''
    try:
        lcolortemp = light.colortemp
    except:
        lcolortemp = 0
    try:
        leffect = light.effect
    except:
        leffect = ''

    #Update database
    cur.execute('INSERT OR IGNORE INTO lights (light_id, name, ltype, reachable, onstate, alert, brightness, colormode, colortemp, hue, sat, xyvalue, effect) \
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', \
        (lid, lname, ltype, lreachable, lon, lalert, lbrightness, lcolormode, lcolortemp, lhue, lsaturation, str(lxy), leffect) )

    cur.execute('UPDATE lights SET light_id = ?, onstate = ?, alert = ?, brightness = ?, colortemp = ?, hue = ?, sat = ?, xyvalue = ?, effect = ?  WHERE name = ?', \
        (lid, lon, lalert, lbrightness, lcolortemp, lhue, lsaturation, str(lxy), leffect, lname))

conn.commit()
print('Lights retrieved.')

#Retrieve Sensors
print('Retrieving sensors...')
sensors = b.get_sensor_objects()

for sensor in sensors:
    sid = sensor.sensor_id
    sname = sensor.name
    smodelid = sensor.modelid
    sswversion = sensor.swversion
    stype = sensor.type
    smanufacturername = sensor.manufacturername
    sstate = sensor.state
    sconfig = sensor.config

    cur.execute('INSERT OR IGNORE INTO sensors (sensor_id, name, modelid, swversion, stype, manufacturername) \
        VALUES (?, ?, ?, ?, ?, ?)', (sid, sname, smodelid, sswversion, stype, smanufacturername))

    cur.execute('UPDATE sensors SET sensor_id = ?, modelid = ?, swversion = ?, stype = ?, manufacturername = ? WHERE name = ? ', \
        (sid, smodelid, sswversion, stype, smanufacturername, sname))

    cur.execute('SELECT id FROM sensors WHERE name = ?', (sname, ))
    row = cur.fetchone()
    sensor_id = row[0]
    
    for k, v in sstate.items():
        cur.execute('INSERT OR IGNORE INTO sensorstate (sensor_id, stateitem, statevalue) \
        VALUES (?, ?, ?)', (sensor_id, k, v))

        cur.execute('SELECT id FROM sensorstate WHERE sensor_id = ? AND stateitem =?', (sensor_id, k))
        row = cur.fetchone()
        state_id = row[0]
        cur.execute('UPDATE sensorstate SET statevalue = ? WHERE id = ?', (v, state_id))

    for k, v in sconfig.items():
        cur.execute('INSERT OR IGNORE INTO sensorconfig (sensor_id, configitem, configvalue) \
        VALUES (?, ?, ?)', (sensor_id, k, str(v)))

        cur.execute('SELECT id FROM sensorconfig WHERE sensor_id = ? AND configitem =?', (sensor_id, k))
        row = cur.fetchone()
        config_id = row[0]
        cur.execute('UPDATE sensorconfig SET configvalue = ? WHERE id = ?', (str(v), config_id))

conn.commit()
print('Sensors retrieved.')

#Retrieve Groups
print('Retrieving groups')
groupcount = len(b.groups)
if groupcount > 0:
    for group in range(groupcount):
        gname = b.get_group(group, 'name')
        glights = b.get_group(group, 'lights')

        cur.execute('INSERT OR IGNORE INTO groups (name) VALUES (?)', (gname, ))
        
        cur.execute('SELECT id FROM groups WHERE name = ?', (gname, ) )
        row = cur.fetchone()
        group_id = row[0]
        for light in glights:
            cur.execute('INSERT OR IGNORE INTO groupmembers (group_id, light_id) VALUES (?, ?)', (group_id, light) )

    conn.commit()
print('Groups retrieved')

#Retrieve scenes



conn.close()



#ignore testcode after this....
quit()

#____________

## some test code; playing with the api.....
for a in range(12):
    lamp = a % 4
    lamp += 1

    # Turn lamp 1 on/off
    b.set_light(1,'on', lamp == 1)
    # Turn lamp 2 on/off
    b.set_light(2,'on', lamp == 2 )
    # Turn lamp 3 on/off
    b.set_light(3,'on', lamp == 3)
    # Turn lamp 4 on/off
    b.set_light(4,'on', lamp == 4)
    time.sleep(0.2)

# You can also control multiple lamps by sending a list as lamp_id
b.set_light( [1,2,3], 'on', False)

# Get the name of a lamp
b.get_light(1, 'name')
