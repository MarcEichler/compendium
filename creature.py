#!/bin/python2

import re
import json
from bs4 import BeautifulSoup
from objdict import ObjDict

from ddbhelper import *

# Represents an ability or feat
class Ability:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc

        # If this is a weapon attack, parse additional info
        m = re.search("(\w*) Weapon Attack: ([+-]\d*) to hit, reach (.*?), (.*?)\. Hit: (\d*) \((.*?)\) (\w*) damage\s*(plus (\d*) \((.*)\) (.*) damage)?", desc)
        if m:
            self.is_attack = True
            self.attack_type = m.group(1)
            self.to_hit = m.group(2)
            self.reach = m.group(3)
            self.target = m.group(4)
            self.damage = m.group(5)
            self.damage_die = m.group(6)
            self.damage_type = m.group(7)
            # Parse secondary damage
            if len(m.groups()) > 8:
                self.secondary_damage = m.group(9)
                self.secondary_damage_die = m.group(10)
                self.secondary_damage_type = m.group(11)
        else:
            self.is_attack = False

        if desc.startswith("Melee Weapon Attack") or desc.startswith("Ranged Weapon Attack"):
            m = re.search("", desc)

    def __str__(self):
        return self.name

    # Creates a list of Abilities from the given list of [name, descriptions]
    @staticmethod
    def fromList(list):
        abilities = []
        for l in list:
            abilities.append(Ability(l[0], l[1]))
        return abilities


# Defines the attributes of a creature
# The structure is similar to the one found in http://www.dnd5eapi.co/
class Creature(object):
    def __init__(self):
        self.name        = "UNNAMED CREATURE"
        self.size        = ""
        self.type        = ""
        self.subtype     = ""
        self.alignment   = ""
        self.armor_class = ""
        self.hit_points  = ""
        self.hit_dice    = ""
        self.speed 	     = ""

        # Senses, languages, challenge
        self.senses           = ""
        self.languages        = ""
        self.challenge_rating = ""

        # Hash map containing all abilities. The value is a tuple of the ability value and their modifier.
        self.strength     = ""
        self.dexterity    = ""
        self.constitution = ""
        self.intelligence = ""
        self.wisdom       = ""
        self.charisma     = ""

        # Saves
        self.strength_save     = ""
        self.dexterity_save    = ""
        self.constitution_save = ""
        self.intelligence_save = ""
        self.wisdom_save       = ""
        self.charisma_save     = ""

        # Skill boni
        self.acrobatics      = 0
        self.animal_handling = 0
        self.arcana          = 0
        self.athletics       = 0
        self.deception       = 0
        self.history         = 0
        self.insight         = 0
        self.intimidation    = 0
        self.investigation   = 0
        self.medicine        = 0
        self.nature          = 0
        self.perception      = 0
        self.performance     = 0
        self.persuasion      = 0
        self.religion        = 0
        self.sleight_of_hand = 0
        self.stealth         = 0
        self.survival        = 0

        # Vulnerabilites, resistances, immunities
        self.damage_vulnerabilities = ""
        self.damage_resistances     = ""
        self.damage_immunities      = ""
        self.condition_immunities   = ""

        # Feats and actions
        self.special_abilities  = []
        self.actions            = []
        self.legendary_actions  = []
        self.reactions          = []

        # Name of the source book
        self.source = None

        # D&D Beyond URL
        self.url = None

        # Image url
        self.image = None

    def __str__(self):
        return self.name

    # Parses a single D&D Beyond stat card and returns the resulting creature
    @staticmethod
    def fromDDBStatCard(card):
        creature = Creature()

        creature.name   = ddbCreatureName(card)
        creature.url    = ddbLink(card)
        creature.source = ddbSource(card)

        print "\tParsing", creature.name+"..."

        # Parse Stat-Block-Data (AC, HP, Speed, Senses, Language, Challenge)
        stats = ddbParseStats(card)
        creature.size           = stats[DDBStatnames.SIZE]
        creature.type           = stats[DDBStatnames.TYPE]
        creature.subtype        = stats[DDBStatnames.SUBTYPE]
        creature.alignment      = stats[DDBStatnames.ALIGNMENT]
        creature.armor_class    = stats[DDBStatnames.ARMOR_CLASS]
        creature.hit_points     = stats[DDBStatnames.HIT_POINTS]
        creature.hit_dice       = stats[DDBStatnames.HIT_DICE]

        creature.speed           = stats[DDBStatnames.SPEED]
        creature.language        = stats[DDBStatnames.LANGUAGES]
        creature.challenge_rating = stats[DDBStatnames.CHALLENGE_RATING]

        # Parse abilities
        abilities = ddbParseAbilities(card)
        creature.strength       = abilities[DDBStatnames.STRENGTH]
        creature.dexterity      = abilities[DDBStatnames.DEXTERITY]
        creature.constitution   = abilities[DDBStatnames.CONSTITUTION]
        creature.intelligence   = abilities[DDBStatnames.INTELLIGENCE]
        creature.wisdom         = abilities[DDBStatnames.WISDOM]
        creature.charisma       = abilities[DDBStatnames.CHARISMA]

        # Parse Stat-Block-Body (Feats and Actions)
        creature.special_abilities  = Ability.fromList(ddbParseSpecialAbilities(card))
        creature.actions            = Ability.fromList(ddbParseActions(card))
        creature.legendary_actions  = Ability.fromList(ddbParseLegendaryActions(card))
        creature.reactions          = Ability.fromList(ddbParseReactions(card))

        # Search for an image
        creature.image = ddbImage(card)
        if creature.image:
            print "\t\tFound an image"
        
        return creature


    # Returns a JSON object of the creature.
    def json(self):
        return json.dumps(self, default=lambda self: self.__dict__, indent=4, sort_keys=False)

    def toFiveForge(self):
        # Represents the commonly recurring element "xy": { "name": "Xy", "current": "Current Value" }
        class Element(ObjDict):
            def __init__(self, name, current=None):
                ObjDict.__init__(self)
                del self["__type__"] # Delete __type__ field
                self["name"] = name
                if current:
                    self["current"] = current
                return

        data = ObjDict()
        data["_t"] = "c"

        ### INFO BLOCK
        data["info"] = ObjDict()
        info = data["info"]

        # Name
        name = Element("Name", self.name)
        info["name"] = name

        # Img
        img = Element("Artwork", None) # TODO: Add image path
        info["img"] = img

        # Description
        notes = Element("Description")
        info["notes"] = notes

        # Race
        if self.subtype:
            race = Element("Race", self.type + " ("+self.subtype+")")
        else:
            race = Element("Race", self.type)
        info["race"] = race

        # Class
        class_ = Element("Class")
        info["class"] = class_

        # Background
        background = Element("Background")
        info["background"] = background

        # Returns abbreviation of the given alignment. Ex: Lawful Evil -> le
        def shortenAlignment(alignment):
            if alignment == "unaligned":
                return None
            if alignment == "neutral":
                return "tn"
            else:
                words = alignment.split()
                print len(words), alignment
                assert(len(words) == 2)
                return words[0][1].lower() + words[1][1].lower()

        # Alignment
        alignment = Element("Alignment", shortenAlignment(self.alignment))
        info["alignment"] = alignment
        ### END OF INFO BLOCK

        ### EXPERIENCE BLOCK
        data["experience"] = ObjDict()
        experience = data["experience"]

        level = Element("Level", 1)
        experience["level"] = level

        cr = Element("Challenge Rating", 14)
        experience["cr"] = cr

        exp = Element("Experience")
        experience["exp"] = exp
        ### END OF EXPERIENCE BLOCK

        ### ATTRIBUTES BLOCK

        ### END OF ATTRIBUTES BLOCK

        ### TRAITS BLOCK
        
        ### END OF TRAITS BLOCK

        ### PERSONALITY BLOCK
        data["personality"] = ObjDict()
        personality = data["personality"]

        traits = Element("Traits")
        personality["traits"] = traits

        ideals = Element("Ideals")
        personality["ideals"] = ideals

        bonds = Element("Bonds")
        personality["bonds"] = bonds

        flaws = Element("Flaws")
        personality["flaws"] = flaws
        ### END OF PERSONALITY BLOCK

        return data.dumps()
