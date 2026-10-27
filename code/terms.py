"""Matching rules for Devil names and saint names, and the word classes for Devil names.

DEVIL rule (applied to NAME1 and NAME2 of OS Open Names, and to watercourse names in OS Open Rivers):
  * the English word Devil as a word of its own, with or without a possessive or plural:
    Devil, Devil's, Devils, Devils'   (so "Kill Devil Copse" counts; "Mandeville" and "Devilla Forest" do not)
  * Devils- fused to a following word: Devilsden, Devilsmouth, Devilspit, Devilsrest
  * Scots Deil, Deil's, Deils as a word (not Deildre or Deilo, which are Welsh names)
  * Scottish Gaelic Deamhain, Diabhail, Dhiabhail ("of the devil") as a word
  Not searched: Hell, Satan, Old Nick and other names that may or may not refer to the Devil; Welsh diafol,
  diawl and cythraul (none occur in OS Open Names).
SAINT rule (OS Open Names, features that are not settlements): "St", "St." or "Saint" followed by a capitalised
  word, e.g. St Peter's Stone, St Agnes Wood, Point St John. The saint is the next word.
Run the tests: python3 code/terms.py
"""
import re

DEVIL = re.compile(r"\bDevil(?:'s|s'|s|’s)?(?![\w])|\bDevils(?=[a-z])|\bDeil(?:'s|s|’s)?(?![\w])|\b(?:Deamhain|Diabhail|Dhiabhail)\b")
SCOTS = re.compile(r"\bDeil")
GAELIC = re.compile(r"Deamhain|Diabhail|Dhiabhail")
NEAR_MISS = re.compile(r"Devilla|Deildre|Deilo|Mandeville|Demoniac")
SAINT = re.compile(r"(?:^|\s)(?:St\.?|Saint) ([A-Z][a-z]+)")

# Head word after "Devil's" (or the fused or Gaelic form), mapped to a word class. The class describes the image
# the name uses, not where the name came from.
WORD_CLASS = {
    "household": ["Kitchen", "Chair", "Dining Room", "Dressing Room", "Study", "Frying Pan", "Punch Bowl", "Punchbowl",
                  "Kettle", "Caldron", "Oven", "Bellows", "Limekiln", "Mill", "Mills", "Barn", "Peatstack", "Thrashing Floor",
                  "Bowling Green", "Garden", "Cheesewring", "Chimney"],
    "body": ["Elbow", "Teeth", "Heid", "Head", "Mouth", "Footsteps", "Dander", "Slide", "Rest", "Jumps"],
    "hollow": ["Den", "Hole", "Pit", "Dingle", "Bottom", "Pool", "Nook"],
    "earthwork": ["Dyke", "Dike", "Bank", "Bridge", "Arch", "Cauld", "Howe"],
    "hill": ["Hill", "Tor", "Rock", "Point", "Ledge", "Craig", "Druim"],
    "wood": ["Wood", "Copse", "Grove", "Plantation"],
    "water": ["Water", "Brook", "Burn", "Gill", "Loch", "Reach"],
}
CLASS_LABEL = {"household": "Household and work", "body": "Body and movement", "hollow": "Dens, holes and pools",
               "earthwork": "Dykes, banks and bridges", "hill": "Hills, rocks and points", "wood": "Woods and copses",
               "water": "Streams and waters", "other": "Other"}
CLASS_ORDER = ["household", "hollow", "wood", "hill", "body", "earthwork", "water", "other"]
_W = {w: c for c, ws in WORD_CLASS.items() for w in ws}


def is_devil(name):
    return bool(name) and bool(DEVIL.search(name))


def head_word(name1, name2=""):
    """The thing the Devil owns: the word or phrase after the Devil word."""
    for nm in (name2, name1):
        if not nm or not DEVIL.search(nm):
            continue
        if GAELIC.search(nm):
            return "Druim" if nm.startswith("Druim") else "Point"
        m = re.search(r"Devils(?=[a-z])([a-z]+)", nm)
        if m:
            return m.group(1).capitalize()
        rest = DEVIL.split(nm, maxsplit=1)
        after = rest[1].strip() if len(rest) > 1 else ""
        if not after:  # "Kill Devil Copse" has the Devil inside: take the last word
            return nm.split()[-1]
        for k in sorted(_W, key=len, reverse=True):
            if after.startswith(k):
                return k
        return after.split()[0]
    return ""


def word_class(head):
    return _W.get(head, "other")


def saint_of(name):
    m = SAINT.search(name or "")
    return m.group(1) if m else None


if __name__ == "__main__":
    yes = ["Devil's Dyke", "Devils Hole", "Devils' Den", "Kill Devil Copse", "Devilsden Wood", "Deil's Caldron", "Deils Wood",
           "Deil Piece", "Druim an Diabhail", "Bod an Deamhain", "The Devil's Point", "Devil’s Humps"]
    no = ["Devilla Forest", "Stoke Mandeville", "Deildre Wood", "Gallt Deilo", "Demoniac Plantation", "Hell Gill", "Devonport"]
    for n in yes:
        assert is_devil(n), n
    for n in no:
        assert not is_devil(n), n
    T = {("Devil's Punch Bowl", ""): "Punch Bowl", ("Devilsden Wood", ""): "Den", ("Kill Devil Copse", ""): "Copse",
         ("Devil's Hill Wood", ""): "Hill", ("Coire na Ciche", "The Devil's Punchbowl"): "Punchbowl",
         ("Bod an Deamhain", "The Devil's Point"): "Point", ("Druim an Diabhail", ""): "Druim", ("Deil's Mills Wood", ""): "Mills",
         ("The Devil's Dining Room", ""): "Dining Room", ("Devil's Thrashing Floor", ""): "Thrashing Floor",
         ("Devilsrest Bottom", ""): "Rest", ("Devil's Pool Bottom", ""): "Pool"}
    for (a, b), v in T.items():
        assert head_word(a, b) == v, (a, head_word(a, b), v)
    assert saint_of("St Peter's Stone") == "Peter" and saint_of("Point St John") == "John" and saint_of("Saint Ann's Hill") == "Ann"
    assert saint_of("Stoke Wood") is None
    print("terms ok")
