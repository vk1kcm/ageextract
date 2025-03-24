#!/usr/bin/env python3
#
# ageextract.py
# Process FIE XML files for a mixed age event and break out the results into age groups.
#
# Assumptions:
# . Results will be 1,2,3,4,5... ie no dual bronze or third place.
#
# Carl Makin
#
# Age Ranges
# U9 - 7,8 
# U11 - 9,10
# U13 - 11,12
# U15 - 13,14
# U17 - 15,16
# U20 - 17,18, 19
# U23 - 20, 21, 22
# 40+

import argparse
# import re
import xml.etree.ElementTree as ET
import sqlite3
from sqlite3 import Error

numfencers = 0
numimported = 0
numfailed = 0
failedlist = []

parser = argparse.ArgumentParser(
    description='Process FIE XML from a single event and produce rankings based on age categories.'
)
parser.add_argument('-s', '--sequential', help='Output places in strict sequential order, rather than having dual bronze places', action='store_true')
parser.add_argument("xmlfile", help="The xml input file in FIE 2019+ format")
# parser.add_argument("attendees", help="File to store attending members")
args = parser.parse_args()

eventxml = ET.parse(args.xmlfile)
root = eventxml.getroot()
# print("Root: ",root.tag, root.attrib['Date'])

eventname = root.attrib['TitreLong']
eventweapon = root.attrib['Arme']
if eventweapon == 'F':
    eventweapon = "Foil"
elif eventweapon == 'E':
    eventweapon = "Epee"
elif eventweapon == 'S':
    eventweapon = "Sabre"
else:
    eventweapon = "Unknown"
print("Event:", eventname)
print("Weapon:", eventweapon)

(evday, evmon, evyear) = root.attrib['Date'].split(".")
print("Event date:", evday, "/", evmon, "/", evyear)

dbconn = sqlite3.connect(':memory:')
dbcurs = dbconn.cursor()
dbcurs.execute('''CREATE TABLE fencers (name TEXT, age INTEGER, gender TEXT, classification INTEGER);''')

fencerlist = root.find("Tireurs")
for fencer in fencerlist.iter("Tireur"):
#    print(fencer.tag, fencer.attrib)
    numfencers = numfencers + 1
    nom = fencer.get('Nom')
    prenom = fencer.get('Prenom')
    name = prenom + " " + nom
    birthday = fencer.get('DateNaissance')
    (bday, bmon, byear) = birthday.split(".")
    age = int(evyear) - int(byear) - 1
    gender = fencer.get('Sexe')
    classification = fencer.get('Classement')
#    print(prenom, " ", nom, " - ", gender, " : ", age, " = ", classification, " :::: ", evyear, " ", byear)
    try:
        x = classification.isnumeric()
        dbcurs.execute('''
            INSERT INTO fencers VALUES (?, ?, ?, ?);''', (name, age, gender, classification))
        dbconn.commit()
        numimported = numimported + 1
    except (AttributeError):
        numfailed = numfailed + 1
        status = fencer.get('Statut')
        failedlist.append([name, age, gender, classification, status])
        next

print("Number of fencers: ", numfencers)
print("Number imported: ", numimported)
print("Number failed: ", numfailed)
print()
print("Failed entries")
print(",\"Name\",\"Age\",\"Gender\",\"Event Ranking\",\"Status\"")
for failed in failedlist:
    print(",", str(failed).strip("[]").replace("'", "\"").replace(", ", ","), sep="")
print()

print("All Fencers in classification order")
print("\"Event Ranking\",\"Name\",\"Age\",\"Gender\",\"Event Ranking\"")
dbcurs.execute('SELECT * from fencers ORDER BY classification')
fencerlist = dbcurs.fetchall()
for thisfencer in fencerlist:
    print(thisfencer[3], ",", str(thisfencer).strip("()").replace("'", "\"").replace(", ", ","), sep="")
print()

def getresults(minage, maxage, category):
    print(category, "Women - Ages", minage, "to", maxage)
    dbcurs.execute("SELECT * from fencers WHERE age BETWEEN ? AND ? AND gender='F' ORDER BY classification",(minage, maxage))
    fencerlist = dbcurs.fetchall()
    ageclass = 0
    print("\"Age Ranking\",\"Name\",\"Age\",\"Gender\",\"Event Ranking\"")
    for thisfencer in fencerlist:
        ageclass = ageclass + 1
        if (not args.sequential and ageclass == 4):
            print(3, sep='', end='') 
        else:
            print(ageclass, sep='', end='') 
        print(",", str(thisfencer).strip("()").replace("'", "\"").replace(", ", ","), sep="")
    print()

    print(category, "Men - Ages", minage, "to", maxage)
    dbcurs.execute("SELECT * from fencers WHERE age BETWEEN ? AND ? AND gender='M' ORDER BY classification",(minage, maxage))
    fencerlist = dbcurs.fetchall()
    ageclass = 0
    print("\"Age Ranking\",\"Name\",\"Age\",\"Gender\",\"Event Ranking\"")
    for thisfencer in fencerlist:
        ageclass = ageclass + 1
        if (not args.sequential and ageclass == 4):
            print(3, sep='', end='') 
        else:
            print(ageclass, sep='', end='') 
        print(",", str(thisfencer).strip("()").replace("'", "\"").replace(", ", ","), sep="")
    print()

getresults(1, 8, "U9")
getresults(1, 10, "U11")
getresults(9, 12, "U13")
getresults(11, 14, "U15")
getresults(13, 16, "U17")
getresults(15, 19, "U20")
getresults(17, 22, "U23")
getresults(39, 99, "Veteran")

