"""Regression tests for bilingual QStock inventory item resolution."""

import pytest

from src.ai.entity_resolver import aliases_for_tests, resolve_item


# One natural English name for every canonical inventory name in the supplied
# QStock inventory export. These tests ensure each item can be requested in
# English while SQL continues to use the stored French canonical name.
ENGLISH_ITEM_NAMES = {
    "Agraphes": "staples",
    "Pistolet Colle Chaudes": "hot glue gun",
    "Ciseaux": "scissors",
    "Boites Vides": "empty boxes",
    "Tissus pour cadeaux": "gift fabric",
    "Tabouret pour Coran": "quran stand",
    "Décorations Ramadan": "ramadan decorations",
    "Crayon à mine": "pencil",
    "Coupons": "vouchers",
    "Couvertures pour tables": "tablecloths",
    "BonHomme pour Premier Soins": "first aid mannequin",
    "Marqueur pour tableau": "whiteboard markers",
    "Crayons de couleur en bois": "wooden colored pencils",
    "Stylos": "ballpoint pens",
    "Valises": "suitcases",
    "Boite de Recyclage": "recycling bin",
    "Crayons de couleurs feutre": "felt-tip markers",
    "Colles": "school glue",
    "Règles": "rulers",
    " Cônes": "traffic cones",
    "Peinture": "paint",
    "Pinceaux": "paintbrushes",
    "Papier de Couleur": "construction paper",
    "Troueuse pour Papier": "hole punch",
    "Papier": "printer paper",
    "Projecteur": "projector",
    "Effaces": "erasers",
    "Télécomandes pour Télés": "tv remotes",
    "Boules de Cotons": "cotton balls",
    "Cable HDMI à USBC": "hdmi to usb-c cable",
    "Batonnet de café": "coffee stirrers",
    "Ballons de Fêtes": "party balloons",
    "Gonfleur de Ballons": "balloon pump",
    "Bâton de Colles Chaudes": "hot glue sticks",
    "Jeux de Bloc en Bois": "wooden building blocks",
    "Cahier Canada": "canada notebooks",
    "Colle Scintillante": "glitter glue",
    "Mousse Florale": "floral foam",
    "Chandelles": "candles",
    "Scotch": "adhesive tape",
    "Mini-Tableaux Transportable": "portable mini whiteboards",
    "Mirroir": "mirrors",
    "Enveloppes": "envelopes",
    "Cahier Kashef": "kashef notebooks",
    "Stand pour Tableaux": "whiteboard stand",
    "Cerceaux": "hula hoops",
    "Mini-Cerceaux": "mini hoops",
    "Épingles": "straight pins",
    "Cordes": "ropes",
    "Batteries": "batteries",
    "Tic-Tac-Toe": "noughts and crosses",
    "Élastiques": "rubber bands",
    "Aguisoir": "pencil sharpener",
    "Aguisoir Électriques": "electric pencil sharpeners",
    "Exacto": "utility knives",
    "Anti-Brocheurs": "staple removers",
    "Balles de Ping-Pong": "table tennis balls",
    "Paille": "drinking straws",
    "Coton-Tige": "cotton swabs",
    "Papier Drapeau liban": "Lebanese flag paper",
    "Marqueur": "markers",
    "Crayon de Cires": "wax crayons",
    "Brocheurs": "staplers",
    "Trambones": "paper clips",
    "Brillant": "glitter",
    "Punaise": "push pins",
    "Post-It": "sticky notes",
    "Cadenas": "padlocks",
    "Mini-roches": "small rocks",
    "Crème à Raser": "shaving cream",
    "Pinces": "clamps",
    "Rubans": "ribbons",
    "Mini-Vase": "small vase",
    "Arrosoir": "watering can",
    "Fleurs": "flowers",
    "Boite de Construction": "construction box",
    "Armoire de Construction": "construction cabinet",
    "Tapis Casse-Têtes": "puzzle mats",
    "Décoration Ashura": "ashura decorations",
    "Vêtements": "clothing",
    "Ballons ": "sports balls",
    "Extincteur": "fire extinguisher",
    "Tentes": "tents",
    "Ping-Pong": "table tennis table",
    "Couvercles de Boites": "box lids",
    "Anciens Costumes Kashef": "old kashef costumes",
    "Matériel de Construction": "construction materials",
    "Bâtons": "wooden sticks",
    "Machine à Coude automatique": "automatic bending machine",
}


@pytest.mark.parametrize(("canonical", "english_name"), ENGLISH_ITEM_NAMES.items())
def test_every_inventory_item_resolves_from_english(canonical: str, english_name: str) -> None:
    resolved = resolve_item(f"Do we have any {english_name}?")
    assert resolved is not None
    assert resolved.canonical_name == canonical


def test_every_inventory_canonical_name_resolves_in_french() -> None:
    aliases = aliases_for_tests()
    assert set(ENGLISH_ITEM_NAMES).issubset(aliases)
    for canonical in ENGLISH_ITEM_NAMES:
        resolved = resolve_item(f"Avons-nous {canonical.strip()} ?")
        assert resolved is not None
        assert resolved.canonical_name == canonical


def test_accent_and_case_insensitive_english_aliases() -> None:
    assert resolve_item("How many SCISSORS are available?").canonical_name == "Ciseaux"
    assert resolve_item("Do we have a PROJECTOR?").canonical_name == "Projecteur"
    assert resolve_item("Do we have des crayons à mine?").canonical_name == "Crayon à mine"
