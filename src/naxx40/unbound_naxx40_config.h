/*
 * mod-unbound: settings for classic Naxxramas (src/naxx40), in place of mod-individual-progression's
 * progression system that the original scripts were written for. Loaded from mod_unbound.conf
 * (Unbound.Naxx40.*) by src/naxx40/unbound_naxx40_config.cpp.
 */

#ifndef UNBOUND_NAXX40_CONFIG_H
#define UNBOUND_NAXX40_CONFIG_H

class Player;

struct UnboundNaxx40Config
{
    // "Doable" versions of four bosses (off = classic)
    static bool Doable4H;           // Four Horsemen: much lower ability damage, no Void Zones
    static bool DoableGluth;        // Gluth looks for a zombie to eat every 12 s instead of 3 s
    static bool DoablePatchwerk;    // Hateful Strike does 80% of its damage
    static bool DoableRazuvious;    // Disrupting Shout instead of Mana Burn

    // Completed "The Dread Citadel - Naxxramas" (9121, 9122 or 9123, Archmage Angela Dosantos at Light's Hope)
    static bool IsAttuned(Player* player);
    // Playerbot account (Unbound.Naxx40.BotAccountRegex on the account name): taken in with its group
    static bool IsBotAccount(Player* player);
};

#endif
