from otree.api import Currency as c, currency_range, Submission
from . import pages
from ._builtin import Bot
from .models import Constants
import random


class PlayerBot(Bot):

    def set_configs(self, prob, homo, hetero, bots, bots_color, tax,
            tax_cons, tax_prod):
        assert(0 <= prob <= 1)
        assert(homo >= 0)
        assert(hetero >= 0)
        assert(bots in [True, False])
        assert(bots_color in [True, False])
        assert(tax >= 0)
        assert(0 <= tax_cons <= 1)
        assert(0 <= tax_prod <= 1)
        assert(0 <= tax_prod + tax_cons <= 1)
        self.session.config['probability_of_same_group'] = prob
        self.session.config['token_store_cost_homogeneous'] = homo
        self.session.config['token_store_cost_heterogeneous'] = hetero 
        self.session.config['automated_traders'] = bots
        self.session.config['bots_trade_same_color'] = bots_color
        self.session.config['foreign_tax'] = tax
        self.session.config['percent_foreign_tax_consumer'] = tax_cons
        self.session.config['percent_foreign_tax_producer'] = tax_prod

    @staticmethod
    def assert_reflective(a1, a2):
        pass
        # assert(a1.role_pre == a2.other_role_pre)
        # assert(a1.other_role_pre == a2.role_pre)
        # assert(a1.group_color == a2.other_group_color) commented for later
        # assert(a1.other_group_color == a2.group_color)
        # assert(a1.token_color == a2.other_token_color)
        # assert(a1.other_token_color == a2.token_color)

    @staticmethod
    def check_bot_results(bot, config, subsession):
        group_id = bot.participant.vars['group']
        player_groups = subsession.get_groups()
        bot_groups = bot.session.vars['automated_traders']
        
        # get trading partner
        other_group, other_id = bot.session.vars['pairs'][subsession.round_number - 1][
            (group_id, bot.id_in_group - 1)]
        other_player = bot_groups[(other_group, other_id)]

        PlayerBot.assert_reflective(bot, other_player)        
        trade_attempted = bot.trade_attempted
        other_trade_attempted = other_player.trade_attempted
        
        # Assertion tests

        # if bots trade same color is on, ensure bot follows the rule
        if bot.role_pre != bot.other_role_pre \
        and bot.role_pre == 'Producer':
            assert(other_trade_attempted)
            if other_player.token_color != bot.group_color:
                if bot.session.config['bots_trade_same_color']:
                    assert(not trade_attempted)
                else:
                    assert(trade_attempted)
            else:
                assert(trade_attempted)

        if bot.role_pre == bot.other_role_pre:
            assert(not trade_attempted)
            assert(not other_trade_attempted)
        
        # if trade should succeed, it does
        if trade_attempted and other_trade_attempted:
            assert(bot.trade_succeeded)
            assert(other_player.trade_succeeded)
        
        # if trade should not succeed, it doesnt
        # p1 attemtps and p2 does not
        if trade_attempted and not other_trade_attempted:
            assert(not bot.trade_succeeded)
            assert(not other_player.trade_succeeded)
        # p2 attempts and p1 does not
        if not trade_attempted and other_trade_attempted:
            assert(not other_player.trade_succeeded)
            assert(not bot.trade_succeeded)
        # neither player attempts
        if not trade_attempted and not other_trade_attempted:
            assert(not other_player.trade_succeeded)
            assert(not bot.trade_succeeded)

        # # if trade does not succeed, tokens to not switch
        # if not bot.trade_succeeded:
        #     assert(bot.participant.vars['token'] == bot.token_color)
        #     assert(other_player.participant.vars['token'] == other_player.token_color)
        
        # if trade does succeed, tokens to swotch
        if bot.trade_succeeded:
            #print('PLAYER', group_id, bot.id_in_group)
            #print(token_color, bot.token_color)
            #print(other_token_color, bot.other_token_color)
            #print(bot.participant.vars['token'])
            assert(bot.participant.vars['token'] == bot.other_token_color)
            assert(other_player.participant.vars['token'] == bot.token_color)
        
        
        if bot.group_color == bot.other_group_color and bot.role_pre == 'Producer' \
        and bot.other_token_color != bot.group_color:
            tax_prod = c(int(config['foreign_tax'] \
                * config['percent_foreign_tax_producer']))
        else:
            tax_prod = c(0)

        if bot.group_color == bot.other_group_color and bot.role_pre == 'Consumer' \
        and bot.token_color != bot.group_color:
            tax_cons = c(int(config['foreign_tax'] \
                * config['percent_foreign_tax_consumer']))
        else:
            tax_cons = c(0)
        store_homo = c(config['token_store_cost_homogeneous'])
        store_hetero = c(config['token_store_cost_heterogeneous'])

        if bot.trade_succeeded:
            if bot.role_pre == 'Consumer':
                assert(bot.participant.vars['token'] == Constants.trade_good)
                assert(bot.payoff == Constants.reward - tax_cons)
            
            if bot.role_pre == 'Producer':
                assert(bot.participant.vars['token'] == Constants.red \
                    or bot.participant.vars['token'] == Constants.blue)
                assert(bot.payoff == -tax_prod)
       
        if not bot.trade_succeeded:
            if bot.participant.vars['token'] == bot.group_color:
                assert(bot.payoff == -store_homo)
            
            if bot.participant.vars['token'] != bot.group_color \
                and bot.participant.vars['token'] != Constants.trade_good:
                assert(bot.payoff == -store_hetero)
        
        if bot.participant.vars['token'] == Constants.trade_good:
            assert(bot.payoff >= -tax_cons)

    def play_round(self):
        aa = [[0.5, 0, 0], [0.75, 0, 0], [0.75, 1, 2]]
        dd = [True, False]
        ee = [True, False]
        ff = [0, 1]
        gg = [[0, 1], [0.5, 0.5], [1, 0]]

        aaa = len(aa)
        ddd = len(dd)
        eee = len(ee)
        fff = len(ff)
        ggg = len(gg)
        size = aaa*ddd*eee*fff*ggg

        for a in range(aaa):
            for d in range(ddd):
                for e in range(eee):
                    for f in range(fff):
                        for g in range(ggg):
                            index = a*ddd*eee*fff*ggg \
                                + d*eee*fff*ggg \
                                + e*fff*ggg \
                                + f*ggg \
                                + g
                            if self.subsession.round_number % size == index:
                                self.set_configs(*(aa[a]), 
                                    dd[d], ee[e], ff[f], *(gg[g]))


       # case = self.subsession.round_number % 3
       # if case == 0:
       #     self.set_configs(.5, 0, 0, True, False, 0, 0.5, 0.5)
       # elif case == 1:
       #     self.set_configs(.75, 0, 0, True, False, 0, 0.5, 0.5)
       # else:
       #     self.set_configs(.75, 1, 2, True, False, 0, 0.5, 0.5)

        if self.subsession.round_number == 1:
            yield (pages.Introduction)
       
        
        ############## TRADING PAGE #############################
        group_id = self.player.participant.vars['group']
        player_groups = self.subsession.get_groups()
        bot_groups = self.session.vars['automated_traders']
        
        
        # get trading partner
        other_group, other_id = self.session.vars['pairs'][self.round_number - 1][
            (group_id, self.player.id_in_group - 1)]
        if other_group < len(player_groups):
            other_player = player_groups[other_group].get_player_by_id(other_id + 1)
        else:
            other_player = bot_groups[(other_group, other_id)]
        
        # get states before submitting any forms
        group_color = self.player.participant.vars['group_color']
        other_group_color = other_player.participant.vars['group_color']
        token_color = self.player.participant.vars['token']
        other_token_color = other_player.participant.vars['token']
        role_pre = 'Consumer' if token_color != Constants.trade_good else 'Producer'
        other_role_pre = 'Consumer' if other_token_color != Constants.trade_good else 'Producer'
        payoff = self.player.payoff
        money = self.player.participant.payoff
        other_payoff = other_player.payoff if other_player.payoff != None else c(0)
        other_money = other_player.participant.payoff

        # logic for whether you trade or not. 
        if role_pre == other_role_pre:
            trade_attempted = False
            # assert(f'You cannot trade' in self.html)
        else:
            assert(token_color != other_token_color)
            # assert(f'Would you like to offer to trade' in self.html)
            trade_attempted = True if random.random() < 0.8 else False

        # check the html
        # assert(f'Your role is {role_pre}' in self.html)
        # assert(f'Their role is {other_role_pre}' in self.html)

        # play the trading page
        yield (pages.Trade, { 'trade_attempted': trade_attempted })

        ################## RESULTS PAGE ###########################
        # get player groups and bot groups
        group_id = self.player.participant.vars['group']
        player_groups = self.subsession.get_groups()
        bot_groups = self.session.vars['automated_traders']
        
        # if automated traders are on, check results for all bots
        # paired with other bots
        if self.session.config['automated_traders']:
            if group_id == 0 and self.player.id_in_group == 1:
                for t1, t2 in self.session.vars['pairs'][self.round_number - 1].items():
                    t1_group, t1_id = t1
                    t2_group, _ = t2
                    # if both members of the pair are bots
                    if t1_group >= len(player_groups) and t2_group >= len(player_groups):
                        a1 = bot_groups[(t1_group, t1_id)]
                        self.check_bot_results(a1, self.session.config, self.subsession)
        
        # get trading partner
        other_group, other_id = self.session.vars['pairs'][self.round_number - 1][
            (group_id, self.player.id_in_group - 1)]
        if other_group < len(player_groups):
            other_player = player_groups[other_group].get_player_by_id(other_id + 1)
        else:
            other_player = bot_groups[(other_group, other_id)]
        self.assert_reflective(self.player, other_player)
        other_trade_attempted = other_player.trade_attempted
        
        # Assertion tests

        # if other player is bot, and trade is possible, bot should try to trade
        if other_group >= len(player_groups) \
        and token_color != other_token_color:
            if role_pre == 'Producer':
                assert(other_trade_attempted)
            else:
                if other_group_color == token_color:    
                    assert(other_trade_attempted)
                elif self.session.config['bots_trade_same_color']:
                    assert(not other_trade_attempted)
                else:
                    assert(other_trade_attempted)

        # if trade should succeed, it does
        if trade_attempted and other_trade_attempted:
            assert(self.player.trade_succeeded)
            assert(trade_attempted == self.player.trade_attempted)
            assert(role_pre == self.player.role_pre)
            assert(other_role_pre == self.player.other_role_pre)
            assert(self.player.role_pre != self.player.other_role_pre)
            assert(self.player.token_color != self.player.other_token_color)
        
        # if trade should not succeed, it doesnt
        # p1 attemtps and p2 does not
        if trade_attempted and not other_trade_attempted:
            assert(not self.player.trade_succeeded)
            assert(not other_player.trade_succeeded)
        # p2 attempts and p1 does not
        if not trade_attempted and other_trade_attempted:
            assert(not other_player.trade_succeeded)
            assert(not self.player.trade_succeeded)
        # neither player attempts
        if not trade_attempted and not other_trade_attempted:
            assert(not other_player.trade_succeeded)
            assert(not self.player.trade_succeeded)

        # if trade does not succeed, tokens to not switch
        if not self.player.trade_succeeded:
            assert(self.player.participant.vars['token'] == self.player.token_color)
            assert(other_player.participant.vars['token'] == other_player.token_color)
        
        # if trade does succeed, tokens to swotch
        if self.player.trade_succeeded:
            #print('PLAYER', group_id, self.player.id_in_group)
            #print(token_color, self.player.token_color)
            #print(other_token_color, self.player.other_token_color)
            #print(self.player.participant.vars['token'])
            assert(self.player.participant.vars['token'] == self.player.other_token_color)
            assert(other_player.participant.vars['token'] == self.player.token_color)
        
        
        store_homo = c(self.session.config['token_store_cost_homogeneous'])
        store_hetero = c(self.session.config['token_store_cost_heterogeneous'])
        
        if group_color == other_group_color and role_pre == 'Producer' \
        and other_token_color != group_color:
            tax_prod = c(int(self.session.config['foreign_tax'] \
                * self.session.config['percent_foreign_tax_producer']))
        else:
            tax_prod = c(0)

        if group_color == other_group_color and role_pre == 'Consumer' \
        and token_color != group_color:
            tax_cons = c(int(self.session.config['foreign_tax'] \
                * self.session.config['percent_foreign_tax_consumer']))
        else:
            tax_cons = c(0)

        if self.player.trade_succeeded:
            if self.player.role_pre == 'Consumer':
                assert(self.player.participant.vars['token'] == Constants.trade_good)
                assert(self.player.payoff == Constants.reward - tax_cons)
                assert(self.player.payoff != payoff)
            
            if self.player.role_pre == 'Producer':
                assert(self.player.participant.vars['token'] == Constants.red \
                    or self.player.participant.vars['token'] == Constants.blue)
                assert(self.player.payoff == -tax_prod)
       
        if not self.player.trade_succeeded:
            if self.player.participant.vars['token'] == group_color:
                assert(self.player.payoff == -store_homo)
            
            if self.player.participant.vars['token'] != group_color \
                and self.player.participant.vars['token'] != Constants.trade_good:
                assert(self.player.payoff == -store_hetero)
        
        if self.player.participant.vars['token'] == Constants.trade_good:
            assert(self.player.payoff >= -tax_cons)
        
        # assert payoffs get updated as they should
        #if other_group >= len(player_groups):
        #    assert(other_player.participant.payoff == other_money + other_player.payoff)
        #assert(self.player.participant.payoff == money + self.player.payoff)

        # submit the results page
        # yield (pages.Results)
        yield Submission(pages.Results, check_html=False)

