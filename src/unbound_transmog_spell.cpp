/*
 * mod-unbound: "Transmogrify" spell.
 *
 * Casting the spell opens mod-transmog-plus's Transmogrify window anywhere, the same way its
 * /transmog command does (the server still checks Transmog.OpenAnywhere). Every character learns
 * the spell on login. The spell row itself comes from spell_dbc (server) and the client patch
 * built by tools/custom_dbc.py (client).
 */

#include "Player.h"
#include "ScriptMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TransmogAddonProtocol.h"

enum UnboundTransmog
{
    SPELL_UNBOUND_TRANSMOGRIFY = 200200, // keep in sync with tools/custom_dbc.py
};

class spell_unbound_transmogrify : public SpellScript
{
    PrepareSpellScript(spell_unbound_transmogrify);

    void HandleDummy(SpellEffIndex effIndex)
    {
        PreventHitDefaultEffect(effIndex);

        if (Player* player = GetCaster()->ToPlayer())
            TransmogAddon::Dispatch(player, "RequestPortable");
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_unbound_transmogrify::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

class unbound_transmog_player : public PlayerScript
{
public:
    unbound_transmog_player() : PlayerScript("unbound_transmog_player", {
        PLAYERHOOK_ON_LOGIN
    }) { }

    void OnPlayerLogin(Player* player) override
    {
        if (!player->HasSpell(SPELL_UNBOUND_TRANSMOGRIFY))
            player->learnSpell(SPELL_UNBOUND_TRANSMOGRIFY);
    }
};

void AddSC_unbound_transmog_spell()
{
    RegisterSpellScript(spell_unbound_transmogrify);
    new unbound_transmog_player();
}
