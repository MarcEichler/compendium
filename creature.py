#!/bin/python2

import re
import json
import math
from bs4 import BeautifulSoup
from objdict import ObjDict

from ddbhelper import *

# Represents an ability or feat
class Ability:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc
        self.source = None

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
        self.character_level = None
        self.size        = ""
        self.type        = ""
        self.subtype     = None
        self.alignment   = ""
        self.armor_class = ""
        self.hit_points  = ""
        self.hit_points_formula = ""
        self.speed 	     = ""
        self.initiative  = None # Initialtive Modifier

        # Senses, languages, challenge
        self.senses             = ""
        self.languages          = ""
        self.challenge_rating   = None
        self.experience_reward  = None

        # Hash map containing all abilities. The value is a tuple of the ability value and their modifier.
        self.strength     = ""
        self.dexterity    = ""
        self.constitution = ""
        self.intelligence = ""
        self.wisdom       = ""
        self.charisma     = ""

        # Save boni. These are None if the creature is not proficient in the respective ability.
        # Otherwise, it is the total bonus to these saving throws.
        self.strength_save     = None
        self.dexterity_save    = None
        self.constitution_save = None
        self.intelligence_save = None
        self.wisdom_save       = None
        self.charisma_save     = None

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

    # Returns the given name, transformed for use in file names.
    # This replaces forbidden characters, such as /, with a -
    def filename(self):
        return self.name.replace("/", "-")

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

        # Split hit points and hit point formula
        hit_points = stats[DDBStatnames.HIT_POINTS]
        m = re.match("(.*)\s*\((.*)\)", hit_points)
        if not m or m.groups() < 2:
            print "Unable to parse Hit Points!"
            return None
        creature.hit_points = int(m.group(1))
        creature.hit_points_formula = m.group(2)

        creature.speed           = stats[DDBStatnames.SPEED]
        creature.language        = stats[DDBStatnames.LANGUAGES]

        # Split challenge erating and experience reward
        m = re.match("([0-9/]*?)\s\((.*)\s*XP\)", stats[DDBStatnames.CHALLENGE_RATING])
        if not m:
            print "Unable to parse Challenge Rating!"
            return None
        # Transform CR to float
        cr = eval(m.group(1)+".0")
        creature.challenge_rating = cr
        creature.experience_reward = m.group(2)

        # Parse abilities
        abilities = ddbParseAbilities(card)
        creature.strength       = int(abilities[DDBStatnames.STRENGTH])
        creature.dexterity      = int(abilities[DDBStatnames.DEXTERITY])
        creature.constitution   = int(abilities[DDBStatnames.CONSTITUTION])
        creature.intelligence   = int(abilities[DDBStatnames.INTELLIGENCE])
        creature.wisdom         = int(abilities[DDBStatnames.WISDOM])
        creature.charisma       = int(abilities[DDBStatnames.CHARISMA])

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
        if self.image:
            img = Element("Artwork", os.path.join("custom", "monsters", self.filename()+".jpeg")) # TODO: Add image path
        else:
            img = Element("Artwork")
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
            elif len(alignment.split()) == 2:
                words = alignment.split()
                return words[0][0].lower() + words[1][0].lower()
            else:
                return None

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
        attributes = ObjDict()
        data["attributes"] = attributes

        hp = Element("Hit Points", self.hit_points)
        hp["max"] = self.hit_points
        hp["formula"] = self.hit_points_formula
        attributes["hp"] = hp

        hd = Element("Hit Dice")
        attributes["hd"] = hd

        if self.character_level:
            prof_bonus = int(2 + math.floor(self.character_level-1/4))
        else:
            prof_bonus = int(2 + math.floor(self.challenge_rating-1/4))
        proficiency = Element("Proficiency Bonus", prof_bonus)
        attributes["proficiency"] = proficiency

        ac = Element("Armor Class", self.armor_class)
        attributes["ac"] = ac

        # Split speed into regular speed and additional speeds (like flying, swimming, ...)
        m = re.match("(\d*) ft.(,\s*(.*)\s*)", self.speed)
        if m:
            speed = Element("Speed", m.group(1))
            if m.group(3):
                speed["extra"] = m.group(3)
        else:
            speed = Element("Speed")
        attributes["speed"] = speed

        initiative = Element("Initiative", self.initiative)
        attributes["initiative"] = initiative

        offensive = Element("Weapon Modifier")
        attributes["offensive"] = offensive

        spellcasting = Element("Spellcasting Ability")
        attributes["spellcasting"] = spellcasting

        inspiration = Element("Inspiration")
        attributes["inspiration"] = inspiration

        death = Element("Death Saves")
        attributes["death saves"] = death
        ### END OF ATTRIBUTES BLOCK

        ### TRAITS BLOCK
        traits = ObjDict()
        data["traits"] = traits

        size = Element("Size", self.size)
        data["size"] = size

        di = Element("Damage Immunities", self.damage_immunities)
        data["di"] = di

        dr = Element("Damage Resistance", self.damage_resistances)
        data["dr"] = dr

        ci = Element("Condition Immunities", self.condition_immunities)
        data["ci"] = ci

        dv = Element("Damage Vulnerabilities", self.damage_vulnerabilities)
        data["dv"] = dv

        senses = Element("Senses", self.senses)
        data["senses"] = senses

        languages = Element("Languages", self.languages)
        data["languages"] = languages
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

        ### ABILITIES BLOCK
        abilities = ObjDict()
        data["abilities"] = abilities

        def mod(ability):
            return int(ability-10/2)

        def isProficient(save):
            if save == 0 or save == None:
                return 0
            else:
                return 1

        str_ = Element("Strength", self.strength)
        str_mod = ObjDict()
        str_mod["mod"] = mod(self.strength)
        str_["modifiers"] = str_mod
        str_["proficient"] = isProficient(self.strength_save)
        abilities["str"] = str_

        dex = Element("Dexterity", self.dexterity)
        dex_mod = ObjDict()
        dex_mod["mod"] = mod(self.dexterity)
        dex["modifiers"] = dex_mod
        dex["proficient"] = isProficient(self.dexterity_save)
        abilities["dex"] = dex

        con = Element("Constitution", self.constitution)
        con_mod = ObjDict()
        con_mod["mod"] = mod(self.constitution)
        con["modifiers"] = con_mod
        con["proficient"] = isProficient(self.constitution_save)
        abilities["con"] = con

        int_ = Element("Intelligence", self.intelligence)
        int_mod = ObjDict()
        int_mod["mod"] = mod(self.intelligence)
        int_["modifiers"] = int_mod
        int_["proficient"] = isProficient(self.intelligence_save)
        abilities["int"] = int_

        wis = Element("Wisdom", self.wisdom)
        wis_mod = ObjDict()
        wis_mod["mod"] = mod(self.wisdom)
        wis["modifiers"] = wis_mod
        wis["proficient"] = isProficient(self.wisdom_save)
        abilities["wis"] = wis

        cha = Element("Charisma", self.charisma)
        cha_mod = ObjDict()
        cha_mod["mod"] = mod(self.charisma)
        cha["modifiers"] = cha_mod
        cha["proficient"] = isProficient(self.charisma_save)
        abilities["cha"] = cha
        ### END OF ABILITIES BLOCK

        ### SKILLS BLOCK
        skills = ObjDict()
        data["skills"] = skills

        acr = Element("Acrobatics", self.acrobatics != 0)
        acr["ability"] = "dex"
        skills["acr"] = acr

        ani = Element("Animal Handling", self.animal_handling != 0)
        ani["ability"] = "wis"
        skills["ani"] = ani

        arc = Element("Arcana", self.arcana != 0)
        arc["ability"] = "int"
        skills["arc"] = arc

        ath = Element("Athletics", self.athletics != 0)
        ath["ability"] = "str"
        skills["ath"] = ath

        dec = Element("Deception", self.deception != 0)
        dec["ability"] = "cha"
        skills["dec"] = dec

        his = Element("History", self.history != 0)
        his["ability"] = "int"
        skills["his"] = his

        ins = Element("Insight", self.insight != 0)
        ins["ability"] = "wis"
        skills["ins"] = ins

        intim = Element("Intimidation", self.intimidation != 0)
        intim["ability"] = "cha"
        skills["int"] = intim

        inv = Element("Investigation", self.investigation != 0)
        inv["ability"] = "int"
        skills["inv"] = inv

        med = Element("Medicine", self.medicine != 0)
        med["ability"] = "wis"
        skills["med"] = med

        nat = Element("Nature", self.nature != 0)
        nat["ability"] = "int"
        skills["nat"] = nat

        per = Element("Perception", self.perception != 0)
        per["ability"] = "wis"
        skills["per"] = per

        pfm = Element("Performance", self.performance != 0)
        pfm["ability"] = "cha"
        skills["pfm"] = pfm

        prs = Element("Persuasion", self.persuasion != 0)
        prs["ability"] = "cha"
        skills["prs"] = prs

        rel = Element("Religion", self.religion != 0)
        rel["ability"] = "int"
        skills["rel"] = rel

        sle = Element("Sleight of Hand", self.sleight_of_hand != 0)
        sle["ability"] = "dex"
        skills["sle"] = sle

        ste = Element("Stealth", self.stealth != 0)
        ste["ability"] = "dex"
        skills["ste"] = ste

        sur = Element("Survival", self.survival != 0)
        sur["ability"] = "wis"
        skills["sur"] = sur
        ### END OF SKILLS BLOCK

        ### CURRENCY BLOCK
        currency = ObjDict()
        data["currency"] = currency

        pp = Element("Platinum")
        currency["pp"] = pp

        gp = Element("Gold")
        currency["gp"] = gp

        sp = Element("Silver")
        currency["sp"] = sp

        cp = Element("Copper")
        currency["cp"] = cp        
        ### END OF CURRENCY

        ### SPELLS BLOCK
        spells = ObjDict()
        data["spells"] = spells

        spell0 = Element("Cantrip")
        spells["spell0"] = spell0

        spell1 = Element("1st Level")
        spells["spell1"] = spell1
        
        spell2 = Element("2nd Level")
        spells["spell2"] = spell2
        
        spell3 = Element("3rd Level")
        spells["spell3"] = spell3

        spell4 = Element("4th Level")
        spells["spell4"] = spell4

        spell5 = Element("5th Level")
        spells["spell5"] = spell5

        spell6 = Element("6th Level")
        spells["spell6"] = spell6

        spell7 = Element("7th Level")
        spells["spell7"] = spell7

        spell8 = Element("8th Level")
        spells["spell8"] = spell8

        spell9 = Element("9th Level")
        spells["spell9"] = spell9
        ### END OF SPELLS BLOCK

        ### RESOURCES BLOCK
        resources = ObjDict()
        data["resources"] = resources

        legendary = Element("Legendary Actions")
        resources["legendary"] = legendary

        primary = Element("Primary Resource")
        resources["primary"] = primary

        secondary = Element("Secondary Resource")
        resources["secondary"] = secondary
        ### END OF RESOURCES BLOCK

        ### SOURCE
        data["source"] = Element("Source", self.source)

        ### TAGS
        data["tags"] = ObjDict()

        ### INVENTORY BLOCK
        data["inventory"] = []
        inventory = data["inventory"]

        # Add each monster attack as a weapon
        for current in self.actions:
            if current.is_attack:
                feat = ObjDict()
                feat["_t"] = "i"

                info = ObjDict()
                info["name"] = Element("Name", current.name)
                info["img"] = Element("Artwork")
                info["notes"] = Element("Description", current.desc)
                feat["info"] = info

                feat["source"] = Element("Source")
                feat["tags"] = ObjDict()

                feat["tags"] = ObjDict()
                feat["_type"] = "Weapon"

                feat["quantity"] = Element("Quantity", 0)
                feat["price"] = Element("Price", 0)
                feat["weight"] = Element("Weight", 0)

                feat["type"] = Element("Weapon Type")
                feat["hit"] = Element("Attack Bonus", current.to_hit)
                feat["damage"] = Element("Damage", current.damage_die)
                feat["damage"]["type"] = current.damage_type
                feat["damage2"] = Element("Alternate Damage", current.secondary_damage_die)
                feat["damage2"]["type"] = current.secondary_damage_type

                feat["range"] = Element("Range", current.reach)
                feat["properties"] = Element("Properties")
                feat["proficient"] = Element("Proficient", 0)
                feat["modifier"] = Element("Offensive Ability")

                tabs = ObjDict()
                tabs["content-tabs"] = "tab-notes"
                feat["tabs"] = tabs

                inventory.append(feat)

        ## END OF INVENTORY

        ### SPELLBOOK
        data["spellbook"] = []

        ### FEATS BLOCK
        feats = []
        for current in self.special_abilities + self.actions + self.legendary_actions + self.reactions:
            if not current.is_attack:
                feat = ObjDict()
                feat["_t"] = "i"
                
                info = ObjDict()
                info["name"] = Element("Name", current.name)
                info["img"] = Element("Artwork")
                info["notes"] = Element("Description", current.desc)
                feat["info"] = info

                feat["source"] = Element("Source")
                feat["tags"] = ObjDict()
                feat["_type"] = "Feat"
                feat["type"] = Element("Feat Type")
                feat["requirements"] = Element("Requirements")
                feat["time"] = Element("Time")
                feat["cost"] = Element("Ability Cost")

                tabs = ObjDict()
                tabs["content-tabs"] = "tab-notes"
                feat["tabs"] = tabs

                feats.append(feat)
        data["feats"] = feats
        ### END OF FEATS BLOCK

        data["_type"] = "NPC"
        data["_s"] = ObjDict()
        data["_lclock"] = 1
        data["_c"] = "localhost"
        data["_uid"] = None
        data["_sync"] = None

        flags = ObjDict()
        flags["npc"] = 1
        data["_flags"] = flags

        tabs = ObjDict()
        tabs["sidebar-tabs"] = "tab-abilities"
        tabs["content-tabs"] = "tab-spells"
        data["flags"] = flags

        return data
