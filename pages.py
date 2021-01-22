from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants


# Description of the game: How to play and returns expected
class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1 and self.participant.vars['MobilePhones'] is False

    def vars_for_template(self):
        exchange_rate = self.session.config['real_world_currency_per_point']
        players_per_group = Constants.players_per_group
        foreign_tax = self.session.config['foreign_tax']
        perc_f_tax_consumer = self.session.config['percent_foreign_tax_consumer']
        perc_f_tax_producer = self.session.config['percent_foreign_tax_producer']
        store_cost_hom = self.session.config['token_store_cost_homogeneous']
        store_cost_het = self.session.config['token_store_cost_heterogeneous']
        show_foreign_transactions = self.session.config['show_foreign_transactions']

        # Treatment variable: 0 if baseline, 1 if tax treatment, 2 if cost treatment, 3 show foreign trans treatment
        # Baseline Treatment
        perc_taxes = False
        storage_costs = False

        # Tax Treatment
        if perc_f_tax_consumer != 0 or perc_f_tax_producer != 0:
            perc_taxes = True
        # 2 Cost Treatment
        if store_cost_hom != 0 or store_cost_het != 0:
            storage_costs = True

        return dict(participant_id=self.participant.label, exchange_rate=exchange_rate, players_per_group=players_per_group,
                    perc_f_tax_consumer=perc_f_tax_consumer,
                    perc_f_tax_producer=perc_f_tax_producer, foreign_tax=foreign_tax, store_cost_hom=store_cost_hom,
                    store_cost_het=store_cost_het, show_foreign_transactions=show_foreign_transactions,
                    perc_taxes=perc_taxes, storage_costs=storage_costs)


class Trade(Page):
    timeout_seconds = 60
    form_model = 'player'
    form_fields = ['trade_attempted', 'trading']

    def vars_for_template(self):
        # self.session.vars['pairs'] is a list of rounds.
        # each round is a dict of (group,id):(group,id) pairs.
        print(f"DEBUG (pages.py): Current Round is {self.round_number}")
        group_id = self.player.participant.vars['group']
        player_groups = self.subsession.get_groups()
        print(f"DEBUG (pages.py): Player Groups {player_groups}")
        bot_groups = self.session.vars['automated_traders']
        print(f"DEBUG (pages.py): Bot Groups {bot_groups}")

        # special case: one special player gets to tell all the bots paired
        # with other bots, to trade

        # only if the automated trader treatment is on
        if self.session.config['automated_traders']:
            print(f"DEBUG (pages.py): Current player = {self.player.id_in_group}")
            if group_id == 0 and self.player.id_in_group == 1:
                for t1, t2 in self.session.vars['pairs'][self.round_number - 1].items():
                    print(f"DEBUG (pages.py): t1 is {t1} and t2 is {t2}")
                    t1_group, t1_id = t1
                    t2_group, _ = t2
                    # if both members of the pair are bots
                    print(f"DEBUG (pages.py): t1_group is {t1_group} and t2_group is {t2_group}")
                    print(f"DEBUG: bot groups = {bot_groups}")
                    if t1_group >= len(player_groups) and t2_group >= len(player_groups):
                        a1 = bot_groups[(t1_group, t1_id)]
                        a1.trade(self.subsession)

        # gets a another pair
        # the other pair is the pair that is paired with the current player
        # if self.session.config['custom_matching'] is True: # id_in_group used directly
        #     other_group, other_id = self.session.vars['pairs'][self.round_number - 1][
        #         (group_id, self.player.id_in_group)]
        # else: # index used instead of id_in_group
        other_group, other_id = self.session.vars['pairs'][self.round_number - 1][
            (group_id, self.player.id_in_group - 1)]
        print(f"DEBUG (pages.py): Other group = {other_group}")
        if other_group < len(player_groups):
            print(f"DEBUG (pages.py): other_group < len(player_groups) = {other_group < len(player_groups)}")
            other_player = player_groups[other_group].get_player_by_id(other_id + 1)
            print(f"DEBUG (pages.py): other normal player = {other_player}")
        else:
            print(f"DEBUG (pages.py): other_group < len(player_groups) = {other_group < len(player_groups)}")
            other_player = bot_groups[(other_group, other_id)]
            print(f"DEBUG (pages.py): other bot player = {other_player}")

        self.player.my_id_in_group = self.player.id_in_group
        print(f"DEBUG (pages.py): Player id in group = {self.player.id_in_group}")
        self.player.my_group_id = group_id
        print(f"DEBUG (pages.py): Player group id = {group_id}")
        self.player.other_id_in_group = other_id + 1
        print(f"DEBUG (pages.py): Player other id in group = {self.player.other_id_in_group}")
        self.player.other_group_id = other_group
        print(f"DEBUG (pages.py): Player other group id = {other_group}")

        # whatever color token they were assigned in models.py
        self.player.token_color = self.player.participant.vars['token']
        self.player.other_token_color = other_player.participant.vars['token']

        # defining roles as in models.py
        # ensuring opposites, such that half are producers and half are consumers
        self.player.role_pre = 'Consumer' if self.player.participant.vars['token'] != Constants.trade_good else 'Producer'
        self.player.other_role_pre = 'Consumer' if self.player.other_token_color != Constants.trade_good else 'Producer'

        # defining group color as in models.py
        self.player.group_color = self.player.participant.vars['group_color']
        self.player.other_group_color = other_player.participant.vars['group_color']

        if self.session.config['automated_traders'] == True \
                and other_group >= len(player_groups):
            other_player.trade(self.subsession)

        # defining the variables for the instructions template
        exchange_rate = self.session.config['real_world_currency_per_point']
        players_per_group = Constants.players_per_group
        foreign_tax = self.session.config['foreign_tax']
        perc_f_tax_consumer = self.session.config['percent_foreign_tax_consumer']
        perc_f_tax_producer = self.session.config['percent_foreign_tax_producer']
        store_cost_hom = self.session.config['token_store_cost_homogeneous']
        store_cost_het = self.session.config['token_store_cost_heterogeneous']
        show_foreign_transactions = self.session.config['show_foreign_transactions']

        # Treatment variable: 0 if baseline, 1 if tax treatment, 2 if cost treatment, 3 show foreign trans treatment
        # Baseline Treatment
        treatment = 0
        # Tax Treatment
        if perc_f_tax_consumer != 0 and perc_f_tax_producer != 0 and foreign_tax != 0:
            treatment = 1
        # 2 Cost Treatment
        elif store_cost_hom != 0 or store_cost_het != 0:
            treatment = 2
        # 3 Show Foreign Trans Treatment
        elif show_foreign_transactions is True:
            treatment = 3

        return {'participant_id': self.participant.label,
            'role_pre': self.player.role_pre,
            'other_role_pre': self.player.other_role_pre,
            'token_color': self.player.participant.vars['token'],
            'group_color': self.player.participant.vars['group_color'],
            'other_token_color': self.player.other_token_color,
            'other_group_color': self.player.other_group_color,
            'exchange_rate': exchange_rate,
            'players_per_group': players_per_group,
            'perc_f_tax_consumer': perc_f_tax_consumer,
            'perc_f_tax_producer': perc_f_tax_producer,
            'foreign_tax': foreign_tax,
            'store_cost_hom': store_cost_hom,
            'store_cost_het': store_cost_het,
            'show_foreign_transactions': show_foreign_transactions,
            'treatment': treatment
            }

    def before_next_page(self):
        if self.timeout_happened:
            self.player.player_timed_out += 1
            ########33## TESTING PURPOSES ONLY
            #if self.player.role_pre != self.player.other_role_pre:
            #    self.player.trade_attempted = True
            #else:
            #    self.player.trade_attempted = False

            ###### END TESTING PURPOSES ONLY
            self.player.trade_attempted = False

    def is_displayed(self):
        return self.participant.vars['MobilePhones'] is False and self.round_number <= self.session.vars['predetermined_stop']


class ResultsWaitPage(WaitPage):
    body_text = 'Espere a que los otros participantes terminen de decidir'
    # wait_for_all_groups = True

    def after_all_players_arrive(self):
        pass

    def is_displayed(self):
        return self.participant.vars['MobilePhones'] is False and self.round_number <= self.session.vars['predetermined_stop']

class Results(Page):
    timeout_seconds = 1

    def vars_for_template(self):
        group_id = self.player.participant.vars['group'] 
        player_groups = self.subsession.get_groups()
        bot_groups = self.session.vars['automated_traders']
        
        # special case: one special player gets to tell all the bots paired
        # with other bots, to compute results
        if self.session.config['automated_traders']:
            if group_id == 0 and self.player.id_in_group == 1: 
                for t1, t2 in self.session.vars['pairs'][self.round_number - 1].items():
                    t1_group, t1_id = t1
                    t2_group, _ = t2
                    # if both members of the pair are bots
                    if t1_group >= len(player_groups) and t2_group >= len(player_groups):
                        a1 = bot_groups[(t1_group, t1_id)]
                        a1.compute_results(self.subsession, Constants.reward)
        
        # identify trading partner
        # similar to above in Trade()
        # if self.session.config['custom_matching'] is True: # id_in_group used directly
        #     other_group, other_id = self.session.vars['pairs'][self.round_number - 1][
        #         (group_id, self.player.id_in_group)]
        # else: # index used instead of id_in_group
        other_group, other_id = self.session.vars['pairs'][self.round_number - 1][
            (group_id, self.player.id_in_group - 1)]
        
        # get other player object
        if other_group < len(player_groups):
            other_player = player_groups[other_group].get_player_by_id(other_id + 1)
        else:
            other_player = bot_groups[(other_group, other_id)]
            other_player.load_round_data()
            other_player.round_number = self.round_number - 1

        # define initial round payoffs
        round_payoff = c(0)

        # logic for switching objects on trade
        # if both players attempted a trade, it must be true
        # that one is a producer and one is a consumer.
        # Only 1 player performs the switch
        if self.player.trade_attempted and other_player.trade_attempted: 
            # only 1 player actually switches the goods
            if self.player.trade_succeeded is None:

                # switch tokens
                self.player.participant.vars['token'] = self.player.other_token_color
                other_player.participant.vars['token'] = self.player.token_color

                # set players' trade_succeeded field
                self.player.trade_succeeded = True
                other_player.trade_succeeded = True
                if other_group > len(player_groups):
                    other_player.store_round_data()

            ### TREATMENT: TAX ON FOREIGN (OPPOSITE) CURRENCY
            # if the player is the consumer, apply consumer tax to them
            # and apply producer tax to other player

            # FOREIGN TRANSACTION:
            # added condition that both parties the same group color
            if self.player.role_pre == 'Consumer':
                tax_consumer = c(0)
                if self.player.token_color != self.player.other_group_color and \
                        self.player.group_color == self.player.other_group_color:
                    tax_consumer += self.session.config['foreign_tax'] \
                        * self.session.config['percent_foreign_tax_consumer']
                    self.player.tax_paid = tax_consumer
                round_payoff += Constants.reward - tax_consumer
                

            # else if the player is the consumer, opposite
            else:
                tax_producer = c(0)
                if self.player.group_color != self.player.other_token_color and \
                        self.player.group_color == self.player.other_group_color:
                    tax_producer += self.session.config['foreign_tax'] \
                        * self.session.config['percent_foreign_tax_producer']
                    self.player.tax_paid = tax_producer
                round_payoff -= tax_producer

        else:
            self.player.trade_succeeded = False

        # penalties for self
        # if your token matches your group color

        # TOKEN STORE COST:
        # if token held for a round = if trade did not succeed
        # homo: token is your color
        # hetero: token is different color
        if not self.player.trade_succeeded:
            if self.player.participant.vars['token'] == self.participant.vars['group_color']:
                round_payoff -= c(self.session.config['token_store_cost_homogeneous'])
                self.player.storage_cost_paid = self.session.config['token_store_cost_homogeneous']

            elif self.player.participant.vars['token'] != Constants.trade_good:
                round_payoff -= c(self.session.config['token_store_cost_heterogeneous'])
                self.player.storage_cost_paid = self.session.config['token_store_cost_heterogeneous']

        # set payoffs
        self.player.set_payoffs(round_payoff)
        if self.player.trade_succeeded:
            new_token_color = self.player.other_token_color
        else:
            new_token_color = self.player.token_color
            

        # tell bot to compute its own trade
        if self.session.config['automated_traders'] == True \
                and other_group >= len(player_groups):
            other_player.compute_results(self.subsession, Constants.reward)
        return {'participant_id': self.participant.label,
            'token_color': self.player.token_color,
            'other_token_color': self.player.other_token_color,
            'role_pre': self.player.role_pre,
            'other_role_pre': self.player.other_role_pre,
            'trade_attempted': self.player.trade_attempted,
            'group_color': self.player.group_color,
            'trade_succeeded': self.player.trade_succeeded,
            'new_token_color': new_token_color,
            'round_payoff': self.player.payoff,
            'round_number': self.round_number, 
        }

    def is_displayed(self):
        return self.participant.vars['MobilePhones'] is False and self.round_number <= self.session.vars['predetermined_stop']


class PostResultsWaitPage(WaitPage):
    body_text = 'Waiting for other participants to finish viewing results.'
#    wait_for_all_groups = True

    def after_all_players_arrive(self):
        bot_groups = self.session.vars['automated_traders']
        
        # count foreign currency transactions this round
        fc_count = 0
        fc_possible_count = 0

        for p in self.subsession.get_players():
            if p.group_color == p.other_group_color and \
                    p.group_color != p.other_token_color and \
                    p.role_pre == 'Producer':
                if p.trade_attempted:
                    fc_count += 1
                    fc_possible_count += 1
                else:
                    fc_possible_count += 1

        #for b in bot_groups.values():
       #     if b.group_color == b.other_group_color and \
       #             b.group_color != b.other_token_color and \
       #             b.role_pre == 'Producer':
       #         if b.trade_attempted:
       #             fc_count += 1
       #             fc_possible_count += 1
       #         else:
       #             fc_possible_count += 1

        self.subsession.fc_transactions = fc_count
        self.subsession.possible_fc_transactions = fc_possible_count

        # Changes added to make the game show "N.A." in case the denominator for the fc_percent is 0
        # In order to return quickly to the original version in case an error appears, the eli code is on comments
        # To make this work, the fc_transaction_percent field was changed to String

        # if fc_count > 0 and fc_possible_count > 0:
        if fc_possible_count > 0:
            fc_percent = int((fc_count / fc_possible_count)*100)
            self.subsession.fc_transaction_percent = f'{fc_percent}%'
        else:
            self.subsession.fc_transaction_percent = ''#'N.A.'

        """
        fc_percent = 0
        if fc_count > 0 and fc_possible_count > 0:
            fc_percent = fc_count/fc_possible_count
        self.subsession.fc_transaction_percent = int(fc_percent*100)
        """

        if self.subsession.round_number == Constants.num_rounds:
            for bot in bot_groups.values():
                bot.export_data()
            # for p in self.subsession.get_players():
            #    p.participant.payoff *= self.session.config['soles_per_ecu']

    def is_displayed(self):
        return self.participant.vars['MobilePhones'] is False and self.round_number <= self.session.vars['predetermined_stop']


page_sequence = [
    Introduction,
    Trade,
    ResultsWaitPage,
    Results,
    PostResultsWaitPage,
]
