#!/bin/python2

import os
import re
import json
import sys
from bs4 import BeautifulSoup
import collections

from creature import Creature

# The input HTML file downloaded from D&D beyond
infile = "/home/marc/Downloads/creatures.html"
incompendium = "/run/user/1000/gvfs/smb-share:server=192.168.178.34,share=steamapps/GM Forge - Virtual Tabletop/public/packs/D&D 5E.json"

outdir = "/run/user/1000/gvfs/smb-share:server=192.168.178.34,share=steamapps/GM Forge - Virtual Tabletop/public/"

# The output folder. All output files will be put into this folder
outimagedir = os.path.join(outdir, "custom", "monsters")
outcompendium = os.path.join(outdir, "packs", "comp.json")

def addToCompendium(creatures):
    with open(incompendium, "r") as f:
        comp = json.load(f, object_pairs_hook=collections.OrderedDict)

    print "Read compendium"

    comp_monsters = comp["content"]["Monsters"]["data"]
    for creature in creatures:
        comp_monsters.append(creature.toFiveForge())

    # Write modied compendium
    with open(outcompendium, "w") as f:
        json.dump(comp, f, indent=2)

    return

def writeCreatures():
    print "### Writing", len(creatures), "creatures..."
    for c in creatures:
        outfile = os.path.join(outdir, c.filename()+".json")
        print "\tWriting", c.name+"..."
        json = c.json()
        with open(outfile, "w") as fp:
            fp.write(json)

    return
    
def downloadImages():
    print "### Downloading images..."
    for c in creatures:
        if c.image:
            outfile = os.path.join(outimagedir, c.filename()+".jpeg")
            if not os.path.isfile(outfile):
                print "\t"+"Downloading", outfile+"..."
                os.system("wget "+c.image+" -O \""+outfile+"\" > /dev/null")
    print "\tAll images downloaded"

    return

# Parse parameters to get input files
infiles = []
for i in range(1, len(sys.argv)):
    infiles.append(sys.argv[i])

if len(infiles) == 0:
    print "No input files specified."
    exit(1)


creatures = []

for infile in infiles:
    with open(infile) as fp:
        soup = BeautifulSoup(fp, "html.parser")

        # Parse all stat cards
        print "### Parsing file", infile
        for card in soup.select('div[class*=\"Basic-Text-Frame\"]'):
            c = Creature.fromDDBStatCard(card)
            if c:
                creatures.append(c)
            else:
                print "Unable to parse creature!"

        # Create output folder
        if not os.path.exists(outdir):
            print "Creating output folder", outdir
            os.makedirs(outdir)

# Sort creature list
creatures = sorted(creatures, key=lambda creature : creature.name)

# Write all found creatures
addToCompendium(creatures)

downloadImages()

