/*
 * mod-unbound: soloable raid mechanics (src/unbound_solo_raids.cpp), for fixes that live in other scripts.
 */

#ifndef UNBOUND_SOLO_RAIDS_H
#define UNBOUND_SOLO_RAIDS_H

class Map;

// Classic Naxxramas, Thaddius (src/naxx40/boss_thaddius_40.cpp): true while the raid has at most one player
// in it and Unbound.SoloRaid.Thaddius is on. Stalagg and Feugen then don't revive each other and don't
// overload their Tesla Coils when they leave their platforms.
bool UnboundSoloThaddius(Map const* map);

// Classic Naxxramas, Gothik the Harvester (src/naxx40/boss_gothik_40.cpp): true while the raid has at most one
// player in it and Unbound.SoloRaid.Gothik is on. His phase two teleport then keeps the player on his threat
// list (normally it drops everyone on the other side, which with one player empties it and makes him reset).
bool UnboundSoloGothik(Map const* map);

#endif
