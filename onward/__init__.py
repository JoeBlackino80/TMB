"""Onward — mini-SaaS na predaj letových rezervácií (hold PNR) pre víza
a preukázanie ďalšej cesty (proof of onward travel).

Zákazník zaplatí malý poplatok, systém cez Duffel API vytvorí skutočnú
rezerváciu bez vystavenia letenky ("hold order") a pošle mu itinerár
s PNR kódom overiteľným u aerolinky. Rezervácia sama prepadne po uplynutí
lehoty na zaplatenie (typicky 24–72 h) — nič sa neplatí aerolinke.
"""
