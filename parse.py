#!/bin/python2

import os
import re
import json
import sys
from bs4 import BeautifulSoup
from enum import Enum

from creature import Creature

# The input HTML file downloaded from D&D beyond
infile = "/home/marc/Downloads/creatures.html"
incompendium = "/run/user/1000/gvfs/smb-share:server=192.168.178.34,share=steamapps/GM Forge - Virtual Tabletop/public/packs/D&D 5E.json"

# The output folder. All output files will be put into this folder
outdir = os.path.join(".", "Monsters")

# Returns the given name, transformed for use in file names.
# This replaces forbidden characters, such as /, with a -
def toFileName(name):
    return name.replace("/", "-")

def writeCreatures():
    print "### Writing", len(creatures), "creatures..."
    for c in creatures:
        outfile = os.path.join(outdir, toFileName(c.name)+".json")
        print "\tWriting", c.name+"..."
        json = c.json()
        with open(outfile, "w") as fp:
            fp.write(json)

    return
    
def downloadImages():
    print "### Downloading images...", len(creatures)
    for c in creatures:
        if c.image:
            outfile = os.path.join(outdir, toFileName(c.name)+".jpeg")
            if not os.path.isfile(outfile):
                print "\t"+"Downloading", outfile+"..."
                os.system("wget "+c.image+" -O \""+outfile+"\" > /dev/null")
            else:
                print "\t"+outfile, "already downloaded"
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
            print c.toFiveForge()
            exit(1)
            if c:
                creatures.append(c)
            else:
                print "Unable to parse creature!"

        # Create output folder
        if not os.path.exists(outdir):
            print "Creating output folder", outdir
            os.makedirs(outdir)

# Write all found creatures
writeCreatures()

downloadImages()

