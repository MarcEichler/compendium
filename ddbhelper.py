import re

class DDBStatnames(object):
    # Abilities
    STRENGTH        = "STR"
    DEXTERITY       = "DEX"
    CONSTITUTION    = "CON"
    INTELLIGENCE    = "INT"
    WISDOM          = "WIS"
    CHARISMA        = "CHA"

    # Stats
    SIZE        = "Size"
    TYPE        = "Type"
    SUBTYPE     = "Subtype"
    ALIGNMENT   = "Alignment"
    ARMOR_CLASS = "Armor Class"
    HIT_POINTS  = "Hit Points"
    HIT_DICE    = "Hit Dice"
    SPEED       = "Speed"
    SENSES      = "Senses"
    LANGUAGES   = "Languages"
    CHALLENGE_RATING = "Challenge"

# Returns the string, but with unicode characters replaced with their ASCII equivalents
def replaceUnicode(str):
    str = str.replace(u"\u2013", "-")
    str = str.replace(u"\u2014", "-")
    str = str.replace(u"\u2019", "'")
    str = str.replace(u"\u2212", "-")
    return str

def ddbSource(card):
    title = card.find_parent("html").head.title
    m = re.search(".*\s*-\s*(.*)\s*- Rules - Compendium - D&D Beyond", title.text)
    if m:
        return m.group(1)
    else:
        return None

def ddbCreatureName(card):
    title = card.find("p", "Stat-Block-Styles_Stat-Block-Title")
    return replaceUnicode(title.get_text())

def ddbLink(card):
    title = card.find("p", "Stat-Block-Styles_Stat-Block-Title")
    link  = title.find("a")
    return link["href"] if link else None

def ddbImage(card):
    img = card.find("img")
    if img:
        link = img.find_parent("a")
        if link:
            return link["href"]

##########################################################################################################
### PARSE STATS
##########################################################################################################
def ddbParseStats(card):
    print "\t\tParsing stats..."

    stats = {}

    # Get and split long type information
    long_type = card.find("p", "Stat-Block-Styles_Stat-Block-Metadata").get_text()
    m = re.match("(?P<size>\w*)\s*(?P<type>.*)\s*(?P<sub>\(.*\))?\s*,\s*(?P<alignment>.*)", long_type)
    if m:
        stats[DDBStatnames.SIZE] = m.group("size")
        stats[DDBStatnames.TYPE] = m.group("type")
        stats[DDBStatnames.SUBTYPE] = m.group("sub") if m.group("sub") else ""
        stats[DDBStatnames.ALIGNMENT] = m.group("alignment")
    else:
        print "Unable to parse type!"
        return None

    # Parse all information from blocks
    for block in card.find_all("p", {"class": [ "Stat-Block-Styles_Stat-Block-Data", "Stat-Block-Styles_Stat-Block-Data-Last"]} ):
        # If there is a string here, take it as value
        string = block.find(text = True, recursive=False)
        val = string.string if string and string.string else ""

        # Parsing these stats from the Monster Manual is a pain in the ass.
        # Ususally, the attribute name is found in one or more spans with the Bold class, the value is found in
        # other, non-bold spans or as string.
        # However, sometimes the header is not bold, or only partially bold. We must account for these bugs manually

        # If we do not find any bold spans, we assume all spans are for the stat name
        forceHeaderSpan = block.find("span", "Sans-Serif-Character-Styles_Bold-Sans-Serif") == None

        # Aggregate all spans
        att = ""
        for span in block.find_all("span"):
            if forceHeaderSpan or ("class" in span.attrs and "Sans-Serif-Character-Styles_Bold-Sans-Serif" in span["class"]):
                att = att + span.text
            else:
                val = val + span.text

        att = att.strip()
        val = replaceUnicode(val.strip())

        # Fix bugs
        # Sometimes, "Armor" and "Class" are divided among name and value.
        if att == "Armor" and "Class" in val:
            att = DDBStatnames.ARMOR_CLASS
            val = val[:6]
        # Sometimes, "Hit" and "Points" are arbitrarily divided among header and value
        if att != DDBStatnames.HIT_POINTS and DDBStatnames.HIT_POINTS.startswith(att) and DDBStatnames.HIT_POINTS in att+val:
            full = att + val
            att = DDBStatnames.HIT_POINTS
            val = full[len(att):].strip()

        # Split "Hit Points" field into hit points and hit dice
        if att == DDBStatnames.HIT_POINTS:
            m = re.match("(.*)\s*\((.*)\)", val)
            if not m or m.groups() < 2:
                print "Unable to parse Hit Points!"
                return None

            stats[DDBStatnames.HIT_POINTS] = m.group(1)
            stats[DDBStatnames.HIT_DICE] = m.group(2)

        stats[att] = val

    return stats


##########################################################################################################
### PARSE ABILITIES
##########################################################################################################
def ddbParseAbilities(card):
    print "\t\tParsing abilities..."

    abilities = {}

    for block in card.find_all("div", { "class" : [ "stat-block-ability-scores-stat", "stat-block-ability-scores"] }):
        # print "BLOCK", block
        att = block.find("div", "stat-block-ability-scores-heading").string.strip()
        val = block.find("span", "stat-block-ability-scores-score").string.strip()

        abilities[att] = val

    return abilities


##########################################################################################################
### PARSE SPECIAL ABILITIES
##########################################################################################################
def ddbParseSpecialAbilities(card):
    print "\t\tParsing special abilities..."

    list = []

    # Process all paragraphs until we find a header
    blocks = card.find_all("p", {'class':["Stat-Block-Styles_Stat-Block-Body", "Stat-Block-Styles_Stat-Block-Body-Last--apply-before-heading-",
                                          "Stat-Block-Styles_Stat-Block-Heading", "Stat-Block-Styles_Stat-Block-Heading--after-last-bar-"]})
    for block in blocks:
        nametag = block.find("span", "Sans-Serif-Character-Styles_Inline-Subhead-Sans-Serif")
        if nametag:
            # Grab name and description
            name = replaceUnicode(nametag.text.strip())

            print "\t\t  >", name
            nametag.extract() # Temporarily remove the nametag, because it makes parsing easier
            desc = block.get_text().strip() # Get the data without the name tag
            desc = desc.replace("\n", "") # Remove newlines
            block.insert(0, nametag) # Re-add nametag

            desc = replaceUnicode(desc)

            list.append([name, desc])
        elif "Stat-Block-Styles_Stat-Block-Heading" in block["class"] \
                or "Stat-Block-Styles_Stat-Block-Heading--after-last-bar-" in block["class"]:
            break

    return list


##########################################################################################################
### PARSE ACTIONS
##########################################################################################################
def ddbParseActions(card):
    print "\t\tParsing actions..."

    list = []

    # Find the "Actions" header
    header = card.find("p", {'class':["Stat-Block-Styles_Stat-Block-Heading", "Stat-Block-Styles_Stat-Block-Heading--after-last-bar-"]},
                            text = "Actions")
    if not header:
        print "\t\t  > No reactions."
        return list

    # Process all paragraphs until we find a header
    blocks = header.find_next_siblings("p", {'class':["Stat-Block-Styles_Stat-Block-Body", "Stat-Block-Styles_Stat-Block-Body-Last--apply-before-heading-",
                                          "Stat-Block-Styles_Stat-Block-Heading", "Stat-Block-Styles_Stat-Block-Heading--after-last-bar-"]})
    for block in blocks:
        nametag = block.find("span", "Sans-Serif-Character-Styles_Inline-Subhead-Sans-Serif")
        if nametag:
            # Grab name and description
            name = replaceUnicode(nametag.text.strip())

            print "\t\t  >", name
            nametag.extract() # Temporarily remove the nametag, because it makes parsing easier
            desc = block.get_text().strip() # Get the data without the name tag
            desc = desc.replace("\n", "") # Remove newlines
            block.insert(0, nametag) # Re-add nametag

            # If the next blocks do not contain a header, we must aggregate them into this ability. This is the case
            # for complex abilities, like the Beholder's Eye Rays, whose descriptions span several paragraphs.
            for sibling in block.find_next_siblings("p"):
                if "class" in sibling.attrs and ("Stat-Block-Styles_Stat-Block-Body" in sibling["class"]
                    or "Stat-Block-Styles_Stat-Block-Body-Last--apply-before-heading-" in sibling["class"]) \
                        and not sibling.find("span", "Sans-Serif-Character-Styles_Inline-Subhead-Sans-Serif"):
                    desc = desc + "\n" + sibling.text
                else:
                    break

            desc = replaceUnicode(desc)

            list.append([name, desc])
        elif "Stat-Block-Styles_Stat-Block-Heading" in block["class"] \
                or "Stat-Block-Styles_Stat-Block-Heading--after-last-bar-" in block["class"]:
            break

    return list


##########################################################################################################
### PARSE LEGENDARY ACTIONS
##########################################################################################################
def ddbParseLegendaryActions(card):
    print "\t\tParsing legendary actions..."

    list = []

    # Find the "Actions" header
    header = card.find("p", "Stat-Block-Styles_Stat-Block-Heading", text = "Legendary Actions")
    if not header:
        print "\t\t  > No legendary actions."
        return list

    # Process all paragraphs until we find a header
    blocks = header.find_next_siblings("p", "Stat-Block-Styles_Stat-Block-Hanging")
    for block in blocks:
        nametag = block.find("span", "Sans-Serif-Character-Styles_Bold-Sans-Serif")
        if nametag:
            # Grab name and description
            name = replaceUnicode(nametag.text.strip())

            print "\t\t  >", name
            nametag.extract() # Temporarily remove the nametag, because it makes parsing easier
            desc = block.get_text().strip() # Get the data without the name tag
            desc = desc.replace("\n", "") # Remove newlines
            block.insert(0, nametag) # Re-add nametag

            desc = replaceUnicode(desc)

            list.append([name, desc])
        elif "Stat-Block-Styles_Stat-Block-Heading" in block["class"] \
                or "Stat-Block-Styles_Stat-Block-Heading--after-last-bar-" in block["class"]:
            break

    return list


##########################################################################################################
### PARSE REACTIONS
##########################################################################################################
def ddbParseReactions(card):
    print "\t\tParsing reactions..."

    list = []

    # Find the "Actions" header
    header = card.find("p", {'class':["Stat-Block-Styles_Stat-Block-Heading", "Stat-Block-Styles_Stat-Block-Heading--after-last-bar-"]},
                       text = "Reactions")
    if not header:
        print "\t\t  > No reactions."
        return list

    # Process all paragraphs until we find a header
    blocks = header.find_next_siblings("p", {'class':["Stat-Block-Styles_Stat-Block-Body", "Stat-Block-Styles_Stat-Block-Body-Last--apply-before-heading-",
                                                      "Stat-Block-Styles_Stat-Block-Heading", "Stat-Block-Styles_Stat-Block-Heading--after-last-bar-"]})
    for block in blocks:
        nametag = block.find("span", "Sans-Serif-Character-Styles_Inline-Subhead-Sans-Serif")
        if nametag:
            # Grab name and description
            name = replaceUnicode(nametag.text.strip())

            print "\t\t  >", name
            nametag.extract() # Temporarily remove the nametag, because it makes parsing easier
            desc = block.get_text().strip() # Get the data without the name tag
            desc = desc.replace("\n", "") # Remove newlines
            block.insert(0, nametag) # Re-add nametag

            # If the next blocks do not contain a header, we must aggregate them into this ability. This is the case
            # for complex abilities, like the Beholder's Eye Rays, whose descriptions span several paragraphs.
            for sibling in block.find_next_siblings("p"):
                if "class" in sibling.attrs and ("Stat-Block-Styles_Stat-Block-Body" in sibling["class"]
                                                 or "Stat-Block-Styles_Stat-Block-Body-Last--apply-before-heading-" in sibling["class"]) \
                        and not sibling.find("span", "Sans-Serif-Character-Styles_Inline-Subhead-Sans-Serif"):
                    desc = desc + "\n" + sibling.text
                else:
                    break

            desc = replaceUnicode(desc)

            list.append([name, desc])
        elif "Stat-Block-Styles_Stat-Block-Heading" in block["class"] \
                or "Stat-Block-Styles_Stat-Block-Heading--after-last-bar-" in block["class"]:
            break


    return list

