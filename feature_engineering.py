import ipaddress
import re
from urllib.parse import urlparse


SUSPICIOUS_KEYWORDS = [
    "login",
    "verify",
    "secure",
    "account",
    "update",
    "signin",
    "confirm",
    "password",
    "payment",
    "bank",
    "support",
    "credential",
]


def normalize_url(url):
    """
    Nettoie l'URL et ajoute un protocole si aucun n'est présent.
    Cela permet à urlparse() d'identifier correctement le domaine.
    """
    url = str(url).strip()

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    return url


def contains_ip_address(hostname):
    """
    Retourne 1 si le domaine est une adresse IP, sinon 0.
    """
    try:
        ipaddress.ip_address(hostname)
        return 1
    except ValueError:
        return 0


def count_subdomains(hostname):
    """
    Compte approximativement le nombre de sous-domaines.

    Exemple :
    google.com -> 0
    mail.google.com -> 1
    login.security.google.com -> 2
    """
    hostname = hostname.lower().strip(".")

    if not hostname:
        return 0

    if contains_ip_address(hostname):
        return 0

    parts = hostname.split(".")

    return max(len(parts) - 2, 0)


def count_special_characters(url):
    """
    Compte les caractères qui ne sont ni des lettres ni des chiffres.
    """
    return len(re.findall(r"[^a-zA-Z0-9]", url))


def count_suspicious_keywords(url):
    """
    Compte le nombre de mots-clés suspects présents dans l'URL.
    """
    url_lower = url.lower()

    return sum(
        keyword in url_lower
        for keyword in SUSPICIOUS_KEYWORDS
    )


def extract_features(url):
    """
    Transforme une URL en caractéristiques numériques.
    """

    original_url = str(url).strip()
    normalized_url = normalize_url(original_url)

    parsed_url = urlparse(normalized_url)

    hostname = parsed_url.hostname or ""
    path = parsed_url.path or ""
    query = parsed_url.query or ""

    number_of_letters = sum(
        character.isalpha()
        for character in original_url
    )

    number_of_digits = sum(
        character.isdigit()
        for character in original_url
    )

    url_length = len(original_url)

    return {
        "url_length": url_length,
        "domain_length": len(hostname),
        "path_length": len(path),
        "query_length": len(query),

        "number_of_subdomains": count_subdomains(hostname),
        "has_ip_address": contains_ip_address(hostname),

        "uses_https": int(
            original_url.lower().startswith("https://")
        ),

        "number_of_letters": number_of_letters,
        "number_of_digits": number_of_digits,
        "number_of_special_characters": count_special_characters(
            original_url
        ),

        "letter_ratio": (
            number_of_letters / url_length
            if url_length > 0
            else 0
        ),

        "digit_ratio": (
            number_of_digits / url_length
            if url_length > 0
            else 0
        ),

        "number_of_dots": original_url.count("."),
        "number_of_hyphens": original_url.count("-"),
        "number_of_underscores": original_url.count("_"),
        "number_of_slashes": original_url.count("/"),
        "number_of_question_marks": original_url.count("?"),
        "number_of_equal_signs": original_url.count("="),
        "number_of_ampersands": original_url.count("&"),
        "number_of_at_symbols": original_url.count("@"),

        "suspicious_keyword_count": count_suspicious_keywords(
            original_url
        ),
    }