"""Inventory item entity resolution for the QStock assistant.

This module deterministically resolves common English and French item names
to the canonical inventory names stored in QStock.

Matching is dependency-free and supports accent-insensitive, case-insensitive
queries. Canonical names are preserved exactly as defined in the inventory.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedItem:
    """A resolved inventory item."""

    canonical_name: str
    matched_alias: str
    source: str


_ITEM_ALIASES: dict[str, tuple[str, ...]] = {
    "Agraphes": (
        "agrafe",
        "agrafes",
        "agraffes",
        "staple",
        "staples",
    ),
    "Pistolet Colle Chaudes": (
        "pistolet colle chaude",
        "pistolet à colle chaude",
        "pistolets à colle chaude",
        "hot glue gun",
        "hot glue guns",
        "glue gun",
        "glue guns",
    ),
    "Ciseaux": (
        "ciseau",
        "ciseaux",
        "scissors",
        "pair of scissors",
        "pairs of scissors",
    ),
    "Boites Vides": (
        "boite vide",
        "boîtes vides",
        "boites vides",
        "empty box",
        "empty boxes",
        "cardboard box",
        "cardboard boxes",
    ),
    "Tissus pour cadeaux": (
        "tissu pour cadeau",
        "tissus pour cadeaux",
        "gift fabric",
        "gift fabrics",
        "gift wrapping fabric",
        "fabric for gifts",
    ),
    "Tabouret pour Coran": (
        "tabouret pour coran",
        "support pour coran",
        "quran stool",
        "quran stand",
        "koran stand",
        "quran holder",
    ),
    "Décorations Ramadan": (
        "decoration ramadan",
        "décorations ramadan",
        "ramadan decoration",
        "ramadan decorations",
    ),
    "Crayon à mine": (
        "crayon à mine",
        "crayon a mine",
        "crayons à mine",
        "crayons a mine",
        "pencil",
        "pencils",
        "lead pencil",
        "lead pencils",
        "graphite pencil",
    ),
    "Coupons": (
        "coupon",
        "coupons",
        "ticket",
        "tickets",
        "game coupons",
        "vouchers",
    ),
    "Couvertures pour tables": (
        "couverture pour table",
        "couvertures pour tables",
        "nappe",
        "nappes",
        "table cover",
        "table covers",
        "tablecloth",
        "tablecloths",
    ),
    "BonHomme pour Premier Soins": (
        "bonhomme pour premiers soins",
        "mannequin de premiers soins",
        "first aid mannequin",
        "first aid dummy",
        "first aid training manikin",
    ),
    "Marqueur pour tableau": (
        "marqueur pour tableau",
        "marqueurs pour tableau",
        "whiteboard marker",
        "whiteboard markers",
        "board marker",
        "board markers",
        "dry erase marker",
        "dry erase markers",
    ),
    "Crayons de couleur en bois": (
        "crayon de couleur en bois",
        "crayons de couleur en bois",
        "wooden colored pencils",
        "wooden coloured pencils",
        "colored pencils",
        "coloured pencils",
        "colour pencils",
        "color pencils",
    ),
    "Stylos": (
        "stylo",
        "stylos",
        "pen",
        "pens",
        "ballpoint",
        "ballpoint pen",
        "ballpoint pens",
    ),
    "Valises": (
        "valise",
        "valises",
        "suitcase",
        "suitcases",
        "luggage",
    ),
    "Boite de Recyclage": (
        "boîte de recyclage",
        "boite de recyclage",
        "bac de recyclage",
        "recycling bin",
        "recycling bins",
        "recycling box",
    ),
    "Crayons de couleurs feutre": (
        "crayon de couleur feutre",
        "crayons de couleurs feutre",
        "feutre de couleur",
        "felt crayons",
        "felt tip crayons",
        "felt-tip crayons",
        "felt-tip pens",
        "felt tip pens",
        "felt-tip markers",
        "felt tip markers",
        "markers for coloring",
        "colouring markers",
        "coloring markers",
    ),
    "Colles": (
        "colle",
        "colles",
        "glue",
        "glues",
        "glue sticks",
        "school glue",
    ),
    "Règles": (
        "règle",
        "regle",
        "règles",
        "regles",
        "ruler",
        "rulers",
        "straightedge",
    ),
    " Cônes": (
        "cône",
        "cones",
        "cônes",
        "cone",
        "traffic cones",
        "training cones",
    ),
    "Peinture": (
        "paint",
        "paints",
        "painting paint",
        "peinture",
    ),
    "Pinceaux": (
        "pinceau",
        "pinceaux",
        "paintbrush",
        "paintbrushes",
        "paint brush",
        "paint brushes",
    ),
    "Papier de Couleur": (
        "papier de couleur",
        "papiers de couleur",
        "colored paper",
        "coloured paper",
        "construction paper",
        "color paper",
    ),
    "Troueuse pour Papier": (
        "troueuse pour papier",
        "perforatrice",
        "perforatrice papier",
        "hole punch",
        "hole puncher",
        "paper punch",
        "paper hole punch",
    ),
    "Papier": (
        "papier",
        "paper",
        "sheets of paper",
        "printer paper",
        "copy paper",
    ),
    "Projecteur": (
        "projecteur",
        "projecteurs",
        "projector",
        "projectors",
        "video projector",
        "video projectors",
    ),
    "Effaces": (
        "efface",
        "effaces",
        "gomme",
        "gommes",
        "eraser",
        "erasers",
        "rubber",
    ),
    "Télécomandes pour Télés": (
        "télécommande pour télé",
        "télécommandes pour télés",
        "telecommande",
        "remote control",
        "remote controls",
        "tv remote",
        "tv remotes",
        "television remote",
    ),
    "Boules de Cotons": (
        "boule de coton",
        "boules de cotons",
        "boules de coton",
        "cotton ball",
        "cotton balls",
    ),
    "Cable HDMI à USBC": (
        "câble hdmi à usbc",
        "cable hdmi a usbc",
        "hdmi to usb c cable",
        "hdmi to usb-c cable",
        "hdmi to usbc cable",
        "usb-c hdmi cable",
    ),
    "Batonnet de café": (
        "bâtonnet de café",
        "batonnet de cafe",
        "bâtonnets de café",
        "coffee stirrer",
        "coffee stirrers",
        "coffee sticks",
        "stir sticks",
    ),
    "Ballons de Fêtes": (
        "ballon de fête",
        "ballons de fêtes",
        "party balloon",
        "party balloons",
        "celebration balloons",
    ),
    "Gonfleur de Ballons": (
        "gonfleur de ballon",
        "gonfleur de ballons",
        "balloon pump",
        "balloon pumps",
        "balloon inflator",
    ),
    "Bâton de Colles Chaudes": (
        "bâton de colle chaude",
        "bâtons de colle chaude",
        "bâton de colles chaudes",
        "hot glue stick",
        "hot glue sticks",
        "glue gun sticks",
    ),
    "Jeux de Bloc en Bois": (
        "jeu de blocs en bois",
        "jeux de bloc en bois",
        "wooden block set",
        "wooden block sets",
        "wooden building blocks",
        "wood blocks",
    ),
    "Cahier Canada": (
        "cahier canada",
        "cahiers canada",
        "canada notebook",
        "canada notebooks",
        "exercise book",
    ),
    "Colle Scintillante": (
        "colle scintillante",
        "colle pailletée",
        "glitter glue",
        "glitter glues",
    ),
    "Mousse Florale": (
        "mousse florale",
        "mousse pour fleurs",
        "floral foam",
        "florist foam",
    ),
    "Chandelles": (
        "chandelle",
        "chandelles",
        "bougie",
        "bougies",
        "candle",
        "candles",
    ),
    "Scotch": (
        "ruban adhésif",
        "scotch",
        "tape",
        "adhesive tape",
        "clear tape",
    ),
    "Mini-Tableaux Transportable": (
        "mini tableau transportable",
        "mini-tableaux transportables",
        "portable mini whiteboard",
        "portable mini whiteboards",
        "small portable boards",
    ),
    "Mirroir": (
        "miroir",
        "mirroir",
        "miroirs",
        "mirror",
        "mirrors",
    ),
    "Enveloppes": (
        "enveloppe",
        "enveloppes",
        "envelope",
        "envelopes",
    ),
    "Cahier Kashef": (
        "cahier kashef",
        "cahiers kashef",
        "kashef notebook",
        "kashef notebooks",
    ),
    "Stand pour Tableaux": (
        "support pour tableau",
        "stand pour tableaux",
        "chevalet",
        "chevalets",
        "easel",
        "easels",
        "whiteboard stand",
        "board stand",
    ),
    "Cerceaux": (
        "cerceau",
        "cerceaux",
        "hula hoop",
        "hula hoops",
        "hoop",
        "hoops",
    ),
    "Mini-Cerceaux": (
        "mini-cerceau",
        "mini-cerceaux",
        "mini hoop",
        "mini hoops",
        "small hoops",
    ),
    "Épingles": (
        "épingle",
        "epingles",
        "épingles",
        "pin",
        "pins",
        "straight pins",
    ),
    "Cordes": (
        "corde",
        "cordes",
        "rope",
        "ropes",
        "cord",
        "cords",
    ),
    "Batteries": (
        "batterie",
        "batteries",
        "battery",
        "AA batteries",
    ),
    "Tic-Tac-Toe": (
        "tic-tac-toe",
        "tic tac toe",
        "noughts and crosses",
    ),
    "Élastiques": (
        "élastique",
        "elastiques",
        "élastiques",
        "rubber band",
        "rubber bands",
        "elastic bands",
    ),
    "Aguisoir": (
        "aiguisoir",
        "aguisoir",
        "taille-crayon",
        "taille crayon",
        "pencil sharpener",
        "pencil sharpeners",
    ),
    "Aguisoir Électriques": (
        "aiguisoir électrique",
        "aguisoir électriques",
        "taille-crayon électrique",
        "electric pencil sharpener",
        "electric pencil sharpeners",
    ),
    "Exacto": (
        "exacto",
        "couteau exacto",
        "couteau de précision",
        "utility knife",
        "utility knives",
        "precision knife",
        "craft knife",
    ),
    "Anti-Brocheurs": (
        "anti-brocheur",
        "anti-brocheurs",
        "retire-agrafes",
        "retire agrafes",
        "staple remover",
        "staple removers",
    ),
    "Balles de Ping-Pong": (
        "balle de ping-pong",
        "balles de ping-pong",
        "ping pong ball",
        "ping-pong balls",
        "table tennis balls",
    ),
    "Paille": (
        "paille",
        "pailles",
        "straw",
        "straws",
        "drinking straws",
    ),
    "Coton-Tige": (
        "coton-tige",
        "cotons-tiges",
        "cotton swab",
        "cotton swabs",
        "cotton bud",
        "cotton buds",
        "Q-tips",
    ),
    "Papier Drapeau liban": (
        "papier drapeau liban",
        "papier drapeau du liban",
        "lebanon flag paper",
        "Lebanese flag paper",
        "Lebanon flag craft paper",
    ),
    "Marqueur": (
        "marqueur",
        "marqueurs",
        "marker",
        "markers",
        "felt pen",
        "felt pens",
    ),
    "Crayon de Cires": (
        "crayon de cire",
        "crayons de cires",
        "crayons de cire",
        "wax crayon",
        "wax crayons",
        "crayons",
    ),
    "Brocheurs": (
        "brocheur",
        "brocheurs",
        "agrafeuse",
        "agrafeuses",
        "stapler",
        "staplers",
    ),
    "Trambones": (
        "trombone",
        "trambones",
        "trombones",
        "paper clip",
        "paper clips",
    ),
    "Brillant": (
        "brillant",
        "brillants",
        "paillettes",
        "glitter",
        "craft glitter",
        "sparkles",
    ),
    "Punaise": (
        "punaises",
        "punaise",
        "push pin",
        "push pins",
        "thumbtack",
        "thumbtacks",
    ),
    "Post-It": (
        "post-it",
        "post it",
        "notes autocollantes",
        "sticky note",
        "sticky notes",
        "adhesive notes",
    ),
    "Cadenas": (
        "cadenas",
        "padlock",
        "padlocks",
        "lock",
        "locks",
    ),
    "Mini-roches": (
        "mini-roche",
        "mini-roches",
        "petites roches",
        "mini rocks",
        "small rocks",
        "pebbles",
    ),
    "Crème à Raser": (
        "crème à raser",
        "creme a raser",
        "shaving cream",
        "shaving foam",
    ),
    "Pinces": (
        "pince",
        "pinces",
        "clip",
        "clips",
        "clamp",
        "clamps",
        "tongs",
    ),
    "Rubans": (
        "ruban",
        "rubans",
        "ribbon",
        "ribbons",
        "ribbon rolls",
    ),
    "Mini-Vase": (
        "mini-vase",
        "mini vase",
        "small vase",
        "small vases",
        "vase",
    ),
    "Arrosoir": (
        "arrosoir",
        "watering can",
        "watering cans",
        "plant watering can",
    ),
    "Fleurs": (
        "fleur",
        "fleurs",
        "flower",
        "flowers",
        "artificial flowers",
        "craft flowers",
    ),
    "Boite de Construction": (
        "boîte de construction",
        "boite de construction",
        "construction box",
        "building box",
        "construction kit box",
    ),
    "Armoire de Construction": (
        "armoire de construction",
        "construction cabinet",
        "building cabinet",
        "construction storage cabinet",
    ),
    "Tapis Casse-Têtes": (
        "tapis casse-tête",
        "tapis casse-têtes",
        "puzzle mat",
        "puzzle mats",
        "puzzle floor mat",
        "foam puzzle mat",
    ),
    "Décoration Ashura": (
        "décoration ashura",
        "décorations ashura",
        "ashura decoration",
        "ashura decorations",
    ),
    "Vêtements": (
        "vêtement",
        "vêtements",
        "vetements",
        "clothing",
        "clothes",
        "garments",
        "apparel",
    ),
    "Ballons ": (
        "ballon",
        "ballons",
        "balloon",
        "balloons",
        "sports balls",
    ),
    "Extincteur": (
        "extincteur",
        "extincteurs",
        "fire extinguisher",
        "fire extinguishers",
    ),
    "Tentes": (
        "tente",
        "tentes",
        "tent",
        "tents",
        "canopy tents",
    ),
    "Ping-Pong": (
        "ping-pong",
        "ping pong",
        "table de ping-pong",
        "table tennis",
        "table tennis table",
    ),
    "Couvercles de Boites": (
        "couvercle de boîte",
        "couvercles de boîtes",
        "couvercles de boites",
        "box lid",
        "box lids",
        "container lids",
    ),
    "Anciens Costumes Kashef": (
        "ancien costume kashef",
        "anciens costumes kashef",
        "kashef costume",
        "kashef costumes",
        "old kashef costumes",
        "scout costumes",
    ),
    "Matériel de Construction": (
        "matériel de construction",
        "materiel de construction",
        "construction material",
        "construction materials",
        "building materials",
    ),
    "Bâtons": (
        "bâton",
        "bâtons",
        "batons",
        "stick",
        "sticks",
        "wooden sticks",
    ),
    "Machine à Coude automatique": (
        "machine à coude automatique",
        "machine a coude automatique",
        "automatic elbow machine",
        "automatic bending machine",
    ),
}


def normalize_text(text: str) -> str:
    """Normalize text for case- and accent-insensitive matching."""
    if not isinstance(text, str):
        return ""

    normalized = unicodedata.normalize("NFKD", text.casefold())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


def _normalize(text: str) -> str:
    """Backward-compatible internal alias for normalize_text."""
    return normalize_text(text)


def aliases_for_tests() -> dict[str, tuple[str, ...]]:
    """Return the alias table for regression tests."""
    return _ITEM_ALIASES.copy()


def _build_alias_index() -> dict[str, set[str]]:
    """Build a normalized alias-to-canonical-name index."""
    index: dict[str, set[str]] = {}

    for canonical_name, aliases in _ITEM_ALIASES.items():
        for alias in (canonical_name, *aliases):
            normalized_alias = _normalize(alias)
            if normalized_alias:
                index.setdefault(normalized_alias, set()).add(canonical_name)

    return index


_ALIAS_INDEX = _build_alias_index()


def resolve_item(text: str) -> ResolvedItem | None:
    """Resolve an item mentioned in a French or English user query.

    Matching prefers the longest alias to avoid choosing a broad alias when
    a more specific item name is present. If the best match maps to multiple
    canonical names, the function returns None rather than guessing.
    """
    normalized_text = _normalize(text)
    if not normalized_text:
        return None

    padded_text = f" {normalized_text} "
    matches: list[tuple[int, str, set[str]]] = []

    for alias, canonical_names in _ALIAS_INDEX.items():
        if f" {alias} " in padded_text:
            matches.append((len(alias.split()), alias, canonical_names))

    if not matches:
        return None

    longest_length = max(match[0] for match in matches)
    longest_matches = [match for match in matches if match[0] == longest_length]

    canonical_names = {canonical for _, _, names in longest_matches for canonical in names}

    if len(canonical_names) != 1:
        return None

    canonical_name = next(iter(canonical_names))
    matched_alias = max(
        (alias for _, alias, _ in longest_matches),
        key=len,
    )

    canonical_aliases = {_normalize(name) for name in _ITEM_ALIASES}

    source = "canonical" if matched_alias in canonical_aliases else "alias"

    return ResolvedItem(
        canonical_name=canonical_name,
        matched_alias=matched_alias,
        source=source,
    )
