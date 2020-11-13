from otree.api import Currency as c, currency_range
import pandas as pd
import numpy as np
import datetime
import random
import pickle


class Participant():
    def __init__(self):
        self.vars = {'group': None}
        self.payoff = c(0)


class Constants():
    trade_good = 'Bien de Consumo'


class Round():
    def __init__(self):
        self.role_pre = None
        self.other_role_pre = None
        self.token_color = None
        self.other_token_color = None
        self.group_color = None
        self.other_group_color=None
        self.trade_attempted = None
        self.trade_succeeded = None
        self.payoff = None
        self.cumulative_payoff = None

    def over(self):
        if all(vars(self).values()):
            return True
        return False

    def __str__(self):
        return f'role pre:          {self.role_pre}\n' + \
            f'other role pre:    {self.other_role_pre}\n' + \
            f'token color:       {self.token_color}\n' + \
            f'other token color: {self.other_token_color}\n' + \
            f'group color:       {self.group_color}\n' + \
            f'other group_color: {self.other_group_color}\n' + \
            f'trade attempted:   {self.trade_attempted}\n' + \
            f'trade succeeded:   {self.trade_succeeded}\n' + \
            f'payoff:            {self.payoff}\n' + \
            f'cumulative payoff: {self.cumulative_payoff}\n'


class AutomatedTrader():
    def __init__(self, session, id_in_group, num_rounds, players_per_group):
        self.participant = Participant()
        self.__round_data = [Round() for i in range(num_rounds)]
        self.session = session
        self.id_in_group = id_in_group
        self.round_number = 0
        self.players_per_group = players_per_group

    def dump_round_data(self):
        id_in_session = (self.id_in_group - 1) + (self.players_per_group * self.participant.vars['group'])
        fname = f'{self.session.code}_{id_in_session}.pkl' 
        with open(fname, 'wb') as f:
            pickle.dump(self.__round_data, f)
    
    def load_round_data(self):
        id_in_session = (self.id_in_group - 1) + (self.players_per_group * self.participant.vars['group'])
        fname = f'{self.session.code}_{id_in_session}.pkl' 
        with open(fname, 'rb') as f:
            self.__round_data = pickle.load(f)

    def export_data(self):
        cols = ['participant.id_in_session',
                'participant.payoff',
                'participant.is_automated',
                'player.id_in_group',
                'player.role_pre',
                'player.other_role_pre',
                'player.token_color',
                'player.other_token_color',
                'player.group_color',
                'player.other_group_color',
                'player.trade_attempted',
                'player.trade_succeeded',
                'player.payoff',
                'group.id_in_subsession',
                'subsession.round_number',
                'session.code',
        ]

        df = {}
        self.load_round_data()
        n = len(self.__round_data)
        id_in_session = (self.id_in_group - 1) + (self.players_per_group * self.participant.vars['group'])
        df[cols[0]] = np.full(n, id_in_session)
        df[cols[1]] = np.array([r.cumulative_payoff if r.cumulative_payoff != None\
                else 0* self.session.config['soles_per_ecu'] for r in self.__round_data])
        df[cols[2]] = np.full(n, 1)
        df[cols[3]] = np.full(n, self.id_in_group + 1)
        df[cols[4]] = np.array([r.role_pre for r in self.__round_data])
        df[cols[5]] = np.array([r.other_role_pre for r in self.__round_data])
        df[cols[6]] = np.array([r.token_color for r in self.__round_data])
        df[cols[7]] = np.array([r.other_token_color for r in self.__round_data])
        df[cols[8]] = np.array([r.group_color for r in self.__round_data])
        df[cols[9]] = np.array([r.other_group_color for r in self.__round_data])
        df[cols[10]] = np.array([r.trade_attempted for r in self.__round_data])
        df[cols[11]] = np.array([r.trade_succeeded for r in self.__round_data])
        df[cols[12]] = np.array([r.payoff for r in self.__round_data])
        df[cols[13]] = np.full(n, self.participant.vars['group'] + 1)
        df[cols[14]] = np.array([i for i in range(1, n + 1)])
        df[cols[15]] = np.full(n, self.session.code)
        df = pd.DataFrame(df)
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        df.to_csv(f'dedollarization_{date}_session_{self.session.code}_automated_trader_{id_in_session}.csv')

    def trade(self, subsession):
        self.load_round_data()
        self.round_number = subsession.round_number - 1
        # self.session.vars['pairs'] is a list of rounds.
        # each round is a dict of (group,id):(group,id) pairs.
        group_id = self.participant.vars['group']
        player_groups = subsession.get_groups()
        bot_groups = self.session.vars['automated_traders']
        # gets a another pair
        # the other pair is the pair that is paired with the current player
        other_group, other_id = self.session.vars['pairs'][self.round_number][
            (group_id, self.id_in_group - 1)]
        if other_group < len(player_groups):
            other_player = player_groups[other_group].get_player_by_id(other_id + 1)
        else:
            other_player = bot_groups[(other_group, other_id)]

        # whatever color token they were assigned in models.py
        self.token_color = self.participant.vars['token']
        self.other_token_color = other_player.participant.vars['token']

        # defining roles as in models.py
        # ensuring opposites, such that half are producers and half are consumers
        self.role_pre = 'Consumer' if self.participant.vars['token'] != Constants.trade_good else 'Producer'
        self.other_role_pre = 'Consumer' if self.other_token_color != Constants.trade_good else 'Producer'

        # defining group color as in models.py
        self.group_color = self.participant.vars['group_color']
        self.other_group_color = other_player.participant.vars['group_color']

        #assert (self.token_color != None)
        #assert (self.other_token_color != None)
        #assert (self.role_pre != None)
        #assert (self.other_role_pre != None)
        #assert (self.group_color != None)
        #assert (self.other_group_color != None)

        # logic for whether you trade or not. 
        if self.role_pre == self.other_role_pre:
            self.trade_attempted = False
        else:

            ### TREATMENT: BOTS ONLY ACCEPT THEIR OWN COLOR

            # if "bots only trading the same color (blue)" treatment is on
            if self.session.config['bots_trade_same_color']:

                # BOT is "self": if the other token is blue, then trade
                if self.other_token_color == self.group_color \
                        or self.role_pre == 'Consumer':
                    self.trade_attempted = True

                # if not, then don't
                else:
                    self.trade_attempted = False

            # if "bots only trading the same color (blue)" treatment is off
            # then just always trade
            else:
                self.trade_attempted = True
        self.dump_round_data()
        print(f'Round {self.round_number}, bot {self.id_in_group}, END OF TRADE\n{self.__round_data[self.round_number]}')

    def compute_results(self, subsession, reward):
        self.load_round_data()
        self.round_number = subsession.round_number - 1
        if self.trade_attempted == None:
            self.trade(subsession)
        group_id = self.participant.vars['group'] 
        player_groups = subsession.get_groups()
        bot_groups = self.session.vars['automated_traders']
        
        # identify trading partner
        # similar to above in Trade()
        other_group, other_id = self.session.vars['pairs'][self.round_number][
            (group_id, self.id_in_group - 1)]
        
        # get other player object
        if other_group < len(player_groups):
            other_player = player_groups[other_group].get_player_by_id(other_id + 1)
        else:
            other_player = bot_groups[(other_group, other_id)]
            other_player.load_round_data()
            other_player.round_number = self.round_number
        # define initial round payoffs
        round_payoff = c(0)

        # logic for switching objects on trade
        # if both players attempted a trade, it must be true
        # that one is a producer and one is a consumer.
        # Only 1 player performs the switch
        if self.trade_attempted and other_player.trade_attempted:
            # only 1 player actually switches the goods
            if self.trade_succeeded is None:
                # switch tokens
                self.participant.vars['token'] = self.other_token_color
                other_player.participant.vars['token'] = self.token_color
                # set players' trade_succeeded field
                self.trade_succeeded = True
                other_player.trade_succeeded = True
                if other_group > len(player_groups):
                    other_player.store_round_data()

            ### TREATMENT: TAX ON FOREIGN (OPPOSITE) CURRENCY

            # if the player is the consumer, apply consumer tax to them
            # and apply producer tax to other player

            # FOREIGN TRANSACTION:
            # both parties the same group color
            if self.role_pre == 'Consumer':
                tax_consumer = c(0)
                if self.token_color != self.other_group_color and \
                        self.group_color == self.other_group_color:
                    tax_consumer += self.session.config['foreign_tax'] \
                        * self.session.config['percent_foreign_tax_consumer']
                round_payoff += reward - tax_consumer

            # else if the player is the consumer, opposite
            else:
                tax_producer = c(0)
                if self.group_color != self.other_token_color and \
                        self.group_color == self.other_group_color:
                    tax_producer += self.session.config['foreign_tax'] \
                        * self.session.config['percent_foreign_tax_producer']
                round_payoff -= tax_producer
        
        else:
            self.trade_succeeded = False
        assert(self.trade_succeeded is not None)
        # penalties for self
        # if your token matches your group color

        # TOKEN STORE COST:
        # if token held for a round = if trade did not succeed
        # homo: token is your color
        # hetero: token is different color
        if not self.trade_succeeded:
            if self.participant.vars['token'] == self.participant.vars['group_color']:
                round_payoff -= c(self.session.config['token_store_cost_homogeneous'])

            # if your token matches the opposite group color
            elif self.participant.vars['token'] != Constants.trade_good:
                round_payoff -= c(self.session.config['token_store_cost_heterogeneous'])

        # set payoffs
        self.set_payoffs(round_payoff)
        self.dump_round_data()
        print(f'Round {self.round_number}, bot {self.id_in_group}, END OF RESULTS\n{self.__round_data[self.round_number]}')
    
    def set_payoffs(self, round_payoff):
        self.payoff = round_payoff

    @property
    def payoff(self):
        r = self.__round_data[self.round_number]
        return r.payoff

    @payoff.setter
    def payoff(self, v):
        r = self.__round_data[self.round_number]
        r.payoff = v
        self.participant.payoff += v
        r.cumulative_payoff = self.participant.payoff
    
    
    def in_round(self, n):
        return self.__round_data[n - 1]

    @property
    def role_pre(self):
        r = self.__round_data[self.round_number]
        return r.role_pre

    @role_pre.setter
    def role_pre(self, v):
        r = self.__round_data[self.round_number]
        r.role_pre = v

    @property
    def other_role_pre(self):
        r = self.__round_data[self.round_number]
        return r.other_role_pre

    @other_role_pre.setter
    def other_role_pre(self, v):
        r = self.__round_data[self.round_number]
        r.other_role_pre = v
    
    @property
    def token_color(self):
        r = self.__round_data[self.round_number]
        return r.token_color

    @token_color.setter
    def token_color(self, v):
        r = self.__round_data[self.round_number]
        r.token_color = v

    @property
    def other_token_color(self):
        r = self.__round_data[self.round_number]
        return r.other_token_color

    @other_token_color.setter
    def other_token_color(self, v):
        r = self.__round_data[self.round_number]
        r.other_token_color = v

    @property
    def group_color(self):
        r = self.__round_data[self.round_number]
        return r.group_color

    @group_color.setter
    def group_color(self, v):
        r = self.__round_data[self.round_number]
        r.group_color = v

    @property
    def other_group_color(self):
        r = self.__round_data[self.round_number]
        return r.other_group_color

    @other_group_color.setter
    def other_group_color(self, v):
        r = self.__round_data[self.round_number]
        r.other_group_color = v

    @property
    def trade_attempted(self):
        r = self.__round_data[self.round_number]
        return r.trade_attempted

    @trade_attempted.setter
    def trade_attempted(self, v):
        r = self.__round_data[self.round_number]
        r.trade_attempted = v

    @property
    def trade_succeeded(self):
        r = self.__round_data[self.round_number]
        return r.trade_succeeded

    @trade_succeeded.setter
    def trade_succeeded(self, v):
        r = self.__round_data[self.round_number]
        r.trade_succeeded = v

