"""Inventory item entity resolution for the QStock assistant.

This module resolves bilingual English/French user-facing names to canonical
inventory names stored in QStock. Matching is deterministic and dependency-free.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedItem:
    """Resolved inventory entity."""

    canonical_name: str
    matched_text: str
    source: str


# Canonical names match the French names currently used in QStock inventory.
# Keep aliases broad enough for natural English/French questions, including
# common spelling, accent, singular/plural, and terminology variations.
_ITEM_ALIASES: dict[str, tuple[str, ...]] = {
    "Agraphes": ("agrafe", "agrafes", "agraffes", "staple", "staples"),
    "Pistolet Colle Chaudes": (
        "pistolet colle chaude", "pistolet à colle chaude", "pistolets à colle chaude",
        "hot glue gun", "hot glue guns", "glue gun", "glue guns",
    ),
    "Ciseaux": ("ciseau", "ciseaux", "scissors", "pair of scissors", "pairs of scissors"),
    "Boites Vides": (
        "boite vide", "boîtes vides", "boites vides", "empty box", "empty boxes",
        "cardboard box", "cardboard boxes",
    ),
    "Tissus pour cadeaux": (
        "tissu pour cadeau", "tissus pour cadeaux", "gift fabric", "gift fabrics",
        "gift wrapping fabric", "fabric for gifts",
    ),
    "Tabouret pour Coran": (
        "tabouret pour coran", "support pour coran", "quran stool", "quran stand",
        "koran stand", "quran holder",
    ),
    "Décorations Ramadan": (
        "decoration ramadan", "décorations ramadan", "ramadan decoration",
        "ramadan decorations",
    ),
    "Crayon à mine": (
        "crayon à mine", "crayon a mine", "crayons à mine", "crayons a mine",
        "pencil", "pencils", "lead pencil", "lead pencils", "graphite pencil",
    ),
    "Coupons": ("coupon", "coupons", "ticket", "tickets", "game coupons", "vouchers"),
    "Couvertures pour tables": (
        "couverture pour table", "couvertures pour tables", "nappe", "nappes",
        "table cover", "table covers", "tablecloth", "tablecloths",
    ),
    "BonHomme pour Premier Soins": (
        "bonhomme pour premiers soins", "mannequin de premiers soins",
        "first aid mannequin", "first aid dummy", "first aid training manikin",
    ),
    "Marqueur pour tableau": (
        "marqueur pour tableau", "marqueurs pour tableau", "whiteboard marker",
        "whiteboard markers", "board marker", "board markers", "dry erase marker",
        "dry erase markers",
    ),
    "Crayons de couleur en bois": (
        "crayon de couleur en bois", "crayons de couleur en bois",
        "wooden colored pencils", "wooden coloured pencils", "colored pencils",
        "coloured pencils", "colour pencils", "color pencils",
    ),
    "Stylos": ("stylo", "stylos", "pen", "pens", "ballpoint", "ballpoint pen", "ballpoint pens"),
    "Valises": ("valise", "valises", "suitcase", "suitcases", "luggage"),
    "Boite de Recyclage": (
        "boîte de recyclage", "boite de recyclage", "bac de recyclage",
        "recycling bin", "recycling bins", "recycling box",
    ),
    "Crayons de couleurs feutre": (
        "crayon de couleur feutre", "crayons de couleurs feutre", "feutre de couleur",
        "felt-tip pens", "felt tip pens", "felt-tip markers", "felt tip markers",
        "markers for coloring", "colouring markers", "coloring markers",
    ),
    "Colles": ("colle", "colles", "glue", "glues", "glue sticks", "school glue"),
    "Règles": ("règle", "regle", "règles", "regles", "ruler", "rulers", "straightedge"),
    " Cônes": ("cône", "cones", "cônes", "cone", "traffic cones", "training cones"),
    "Peinture": ("paint", "paints", "painting paint", "peinture"),
    "Pinceaux": ("pinceau", "pinceaux", "paintbrush", "paintbrushes", "paint brush", "paint brushes"),
    "Papier de Couleur": (
        "papier de couleur", "papiers de couleur", "colored paper", "coloured paper",
        "construction paper", "color paper",
    ),
    "Troueuse pour Papier": (
        "troueuse pour papier", "perforatrice", "perforatrice papier", "hole punch",
        "hole puncher", "paper punch", "paper hole punch",
    ),
    "Papier": ("papier", "paper", "sheets of paper", "printer paper", "copy paper"),
    "Projecteur": ("projecteur", "projecteurs", "projector", "projectors", "video projector"),
    "Effaces": ("efface", "effaces", "gomme", "gommes", "eraser", "erasers", "rubber"),
    "Télécomandes pour Télés": (
        "télécommande pour télé", "télécommandes pour télés", "telecommande",
        "remote control", "remote controls", "tv remote", "tv remotes", "television remote",
    ),
    "Boules de Cotons": (
        "boule de coton", "boules de cotons", "boules de coton", "cotton ball",
        "cotton balls",
    ),
    "Cable HDMI à USBC": (
        "câble hdmi à usbc", "cable hdmi a usbc", "hdmi to usb c cable",
        "hdmi to usb-c cable", "hdmi to usbc cable", "usb-c hdmi cable",
    ),
    "Batonnet de café": (
        "bâtonnet de café", "batonnet de cafe", "bâtonnets de café", "coffee stirrer",
        "coffee stirrers", "coffee sticks", "stir sticks",
    ),
    "Ballons de Fêtes": (
        "ballon de fête", "ballons de fêtes", "party balloon", "party balloons",
        "celebration balloons",
    ),
    "Gonfleur de Ballons": (
        "gonfleur de ballon", "gonfleur de ballons", "balloon pump", "balloon pumps",
        "balloon inflator",
    ),
    "Bâton de Colles Chaudes": (
        "bâton de colle chaude", "bâtons de colle chaude", "bâton de colles chaudes",
        "hot glue stick", "hot glue sticks", "glue gun sticks",
    ),
    "Jeux de Bloc en Bois": (
        "jeu de blocs en bois", "jeux de bloc en bois", "wooden block set",
        "wooden block sets", "wooden building blocks", "wood blocks",
    ),
    "Cahier Canada": ("cahier canada", "cahiers canada", "canada notebook", "canada notebooks", "exercise book"),
    "Colle Scintillante": (
        "colle scintillante", "colle pailletée", "glitter glue", "glitter glues",
    ),
    "Mousse Florale": ("mousse florale", "mousse pour fleurs", "floral foam", "florist foam"),
    "Chandelles": ("chandelle", "chandelles", "bougie", "bougies", "candle", "candles"),
    "Scotch": ("ruban adhésif", "scotch", "tape", "adhesive tape", "clear tape"),
    "Mini-Tableaux Transportable": (
        "mini tableau transportable", "mini-tableaux transportables",
        "portable mini whiteboard", "portable mini whiteboards", "small portable boards",
    ),
    "Mirroir": ("miroir", "mirroir", "miroirs", "mirror", "mirrors"),
    "Enveloppes": ("enveloppe", "enveloppes", "envelope", "envelopes"),
    "Cahier Kashef": ("cahier kashef", "cahiers kashef", "kashef notebook", "kashef notebooks"),
    "Stand pour Tableaux": (
        "support pour tableau", "stand pour tableaux", "chevalet", "chevalets",
        "easel", "easels", "whiteboard stand", "board stand",
    ),
    "Cerceaux": ("cerceau", "cerceaux", "hula hoop", "hula hoops", "hoop", "hoops"),
    "Mini-Cerceaux": ("mini-cerceau", "mini-cerceaux", "mini hoop", "mini hoops", "small hoops"),
    "Épingles": ("épingle", "epingles", "épingles", "pin", "pins", "straight pins"),
    "Cordes": ("corde", "cordes", "rope", "ropes", "cord", "cords"),
    "Batteries": ("batterie", "batteries", "battery", "batteries", "AA batteries"),
    "Tic-Tac-Toe": ("tic-tac-toe", "tic tac toe", "noughts and crosses"),
    "Élastiques": ("élastique", "elastiques", "élastiques", "rubber band", "rubber bands", "elastic bands"),
    "Aguisoir": ("aiguisoir", "aguisoir", "taille-crayon", "taille crayon", "pencil sharpener", "pencil sharpeners"),
    "Aguisoir Électriques": (
        "aiguisoir électrique", "aguisoir électriques", "taille-crayon électrique",
        "electric pencil sharpener", "electric pencil sharpeners",
    ),
    "Exacto": ("exacto", "couteau exacto", "couteau de précision", "utility knife", "utility knives", "precision knife", "craft knife"),
    "Anti-Brocheurs": (
        "anti-brocheur", "anti-brocheurs", "retire-agrafes", "retire agrafes",
        "staple remover", "staple removers",
    ),
    "Balles de Ping-Pong": (
        "balle de ping-pong", "balles de ping-pong", "ping pong ball",
        "ping-pong balls", "table tennis balls",
    ),
    "Paille": ("paille", "pailles", "straw", "straws", "drinking straws"),
    "Coton-Tige": ("coton-tige", "cotons-tiges", "cotton swab", "cotton swabs", "cotton bud", "cotton buds", "Q-tips"),
    "Papier Drapeau liban": (
        "papier drapeau liban", "papier drapeau du liban", "lebanon flag paper",
        "Lebanese flag paper", "Lebanon flag craft paper",
    ),
    "Marqueur": ("marqueur", "marqueurs", "marker", "markers", "felt pen", "felt pens"),
    "Crayon de Cires": ("crayon de cire", "crayons de cires", "crayons de cire", "wax crayon", "wax crayons", "crayons"),
    "Brocheurs": ("brocheur", "brocheurs", "agrafeuse", "agrafeuses", "stapler", "staplers"),
    "Trambones": ("trombone", "trambones", "trombones", "paper clip", "paper clips"),
    "Brillant": ("brillant", "brillants", "paillettes", "glitter", "craft glitter", "sparkles"),
    "Punaise": ("punaises", "punaise", "push pin", "push pins", "thumbtack", "thumbtacks"),
    "Post-It": ("post-it", "post it", "notes autocollantes", "sticky note", "sticky notes", "adhesive notes"),
    "Cadenas": ("cadenas", "padlock", "padlocks", "lock", "locks"),
    "Mini-roches": ("mini-roche", "mini-roches", "petites roches", "mini rocks", "small rocks", "pebbles"),
    "Crème à Raser": ("crème à raser", "creme a raser", "shaving cream", "shaving foam"),
    "Pinces": ("pince", "pinces", "clip", "clips", "clamp", "clamps", "tongs"),
    "Rubans": ("ruban", "rubans", "ribbon", "ribbons", "ribbon rolls"),
    "Mini-Vase": ("mini-vase", "mini vase", "small vase", "small vases", "vase"),
    "Arrosoir": ("arrosoir", "watering can", "watering cans", "plant watering can"),
    "Fleurs": ("fleur", "fleurs", "flower", "flowers", "artificial flowers", "craft flowers"),
    "Boite de Construction": (
        "boîte de construction", "boite de construction", "construction box",
        "building box", "construction kit box",
    ),
    "Armoire de Construction": (
        "armoire de construction", "construction cabinet", "building cabinet",
        "construction storage cabinet",
    ),
    "Tapis Casse-Têtes": (
        "tapis casse-tête", "tapis casse-têtes", "puzzle mat", "puzzle mats",
        "puzzle floor mat", "foam puzzle mat",
    ),
    "Décoration Ashura": (
        "décoration ashura", "décorations ashura", "ashura decoration", "ashura decorations",
    ),
    "Vêtements": ("vêtement", "vêtements", "vetements", "clothing", "clothes", "garments", "apparel"),
    "Ballons ": ("ballon", "ballons", "balloon", "balloons", "sports balls"),
    "Extincteur": ("extincteur", "extincteurs", "fire extinguisher", "fire extinguishers"),
    "Tentes": ("tente", "tentes", "tent", "tents", "canopy tents"),
    "Ping-Pong": ("ping-pong", "ping pong", "table de ping-pong", "table tennis", "table tennis table"),
    "Couvercles de Boites": (
        "couvercle de boîte", "couvercles de boîtes", "couvercles de boites",
        "box lid", "box lids", "container lids",
    ),
    "Anciens Costumes Kashef": (
        "ancien costume kashef", "anciens costumes kashef", "kashef costume",
        "kashef costumes", "old kashef costumes", "scout costumes",
    ),
    "Matériel de Construction": (
        "matériel de construction", "materiel de construction", "construction material",
        "construction materials", "building materials",
    ),
    "Bâtons": ("bâton", "bâtons", "batons", "stick", "sticks", "wooden sticks"),
    "Machine à Coude automatique": (
        "machine à coude automatique", "machine a coude automatique",
        "automatic elbow machine", "automatic bending machine",
    ),
}

_GENERIC_ITEM_WORDS = {
    "all", "our", "my", "the", "they", "them", "their", "it", "its", "this",
    "that", "these", "those", "ones", "we", "items", "item", "products",
    "product", "articles", "article", "inventory", "stock", "units", "unit",
    "quantity", "quantities", "quantite", "quantites", "available", "currently",
    "right", "now", "things", "everything", "located", "tout", "tous", "toutes",
    "nos", "inventaire", "unites", "unité", "unités",
}


def normalize_text(value: str) -> str:
    """Normalize accents, punctuation, whitespace and case for matching."""
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("’", "'")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def resolve_item(question: str) -> ResolvedItem | None:
    """Resolve an item entity from a natural-language inventory question.

    Alias matching handles bilingual English/French questions even when the
    database stores only the French canonical name. If no alias matches, an
    explicit item phrase is returned as-is so SQL can search for a real name
    without inventing a translation.
    """
    normalized = normalize_text(question)
    if not normalized:
        return None

    aliases: list[tuple[str, str]] = []
    for canonical, values in _ITEM_ALIASES.items():
        aliases.append((normalize_text(canonical), canonical))
        aliases.extend((normalize_text(alias), canonical) for alias in values)

    for alias, canonical in sorted(aliases, key=lambda pair: len(pair[0]), reverse=True):
        if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", normalized):
            source = "alias" if normalize_text(canonical) != alias else "canonical"
            return ResolvedItem(canonical, alias, source)

    candidate = _extract_explicit_item_phrase(normalized)
    if candidate:
        return ResolvedItem(candidate, candidate, "explicit")
    return None


def aliases_for_tests() -> dict[str, tuple[str, ...]]:
    """Return a copy of the supported alias dictionary for tests/tooling."""
    return {key: tuple(values) for key, values in _ITEM_ALIASES.items()}


def _extract_explicit_item_phrase(text: str) -> str:
    """Extract a subject from common item-specific question forms."""
    patterns = (
        r"^how many (.+?) (?:do|did) (?:we|i) have(?:\s+in stock)?$",
        r"^how many (.+?) (?:are|is) available$",
        r"^where (?:is|are) (?:the )?(.+?)$",
        r"^(?:do|does) (?:we|you) have (?:any )?(?:the )?(.+?)$",
        r"^(?:are|is) (?:the )?(.+?) available$",
        r"^(?:show|list|display) (?:me )?(?:the )?(.+?)(?:\s+available)?$",
        r"^combien (?:de |d')(.+?) (?:avons-nous|avons nous|avons)\b.*$",
        r"^combien (?:de |d')(.+?) (?:sont|est) disponible(?:s)?$",
        r"^(?:ou|où) (?:est|sont) (?:le |la |les )?(.+?)$",
        r"^(?:avons-nous|avons nous) (?:des |du |de la |de l')?(.+?)\??$",
    )
    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        candidate = _clean_candidate(match.group(1).strip(" ?.,!;:"))
        if candidate:
            return candidate
    return ""


def _clean_candidate(candidate: str) -> str:
    words = candidate.split()
    if not words or any(word in _GENERIC_ITEM_WORDS for word in words):
        return ""
    return " ".join(words).strip()
