from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
import copy
import json
from .automated_trader import AutomatedTrader


class ContextSeed:
    """
    context manager to ensure sample draws are
    shared among different agents
    """
    def __init__(self, seed):
        pass
        #self.seed = seed
    
    def __enter__(self):
        pass
        #random.seed(self.seed)
    
    def __exit__(self, *_):
        pass
        #random.seed(random.randint(0, 100))

class Constants(BaseConstants):
    name_in_url = 'dedollarization'
    instructions_button = 'dedollarization/Instructions_Button.html'
    instructions_template = 'dedollarization/Instructions.html'
    contact_template = 'dedollarization/Contactenos.html'
    players_per_group = 8
    # num_rounds = 115 # for production run
    num_rounds = 2 # for demo run
    endowment = c(50)
    reward = c(10)
    red = 'Rojo'
    blue = 'Azul'
    trade_good = 'Bien de Consumo'


class Subsession(BaseSubsession):
    # foreign transaction count for subsession

    fc_transactions = models.IntegerField()
    possible_fc_transactions = models.IntegerField()
    fc_transaction_percent = models.StringField()
    # fc_transaction_percent = models.IntegerField()
    
    def creating_session(self):

        if self.round_number == 1:
            # added predetermined_stop
            self.session.vars['predetermined_stop'] = self.session.config["round_to_stop"]

        # checking if the session is a custom matching one
        if self.session.config['custom_matching'] is True:
            # importing the matching file
            with open(self.session.config['matching_file']) as json_data:
                matching_file = json.load(json_data)

            if self.round_number == 1:
                print('starting create subsession')
                #TODO: edit following lines for grouping

                # puts players into groups of size players_per_group
                self.group_randomly()

                # depends on if traders are on or off
                if self.session.config['automated_traders']:
                    n_groups = len(self.get_groups()) * 2

                else:
                    n_groups = len(self.get_groups())

                # use the custom pairings
                # for the whole session
                self.session.vars['pairs'] = []

                for r in range(Constants.num_rounds):
                    print('starting round for humans', r + 1)
                    # maps traders to their trading partners
                    # (group_id, player_id) <=> (group_id, player_id)
                    # so that a player can look up who their trading partner is
                    # in this map
                    pairs = {}
                    groups = []
                    current_matchings = matching_file["matchings"][r]
                    humans_matchings = current_matchings["humans"] # matchings per group for humans
                    print("DEBUG: Starting human players pairing")
                    for gi in range(n_groups/2): # gi: id of a group
                        # humans paired with other humans
                        for player_id_in_group in range(1, Constants.players_per_group + 1):
                            current_matching = humans_matchings[f"{player_id_in_group}"]
                            # creating the pairs for human matchings
                            if current_matching["partner_type"] == "human":
                                print("DEBUG: human pairing")
                                print(f"DEBUG: Pairs at beginning of Loop = {pairs}")
                                partner_id_in_group = current_matching["partner_id"]
                                pairs[(gi, player_id_in_group)] = (gi, partner_id_in_group)
                                print(f"DEBUG: Pairs during Loop = {pairs}")

                            elif current_matching["partner_type"] == "bot":
                                print("DEBUG: bot pairing")
                                print(f"DEBUG: Pairs at beginning of Loop = {pairs}")
                                partner_id_in_group = current_matching["partner_id"]
                                pairs[(gi, player_id_in_group)] = (gi + round(n_groups/2), partner_id_in_group) # bots group are other half
                                print(f"DEBUG: Pairs during Loop = {pairs}")
                            else:
                                print(f"DEBUG: Undefined partner type = {current_matching['partner_type']}")

                        print(f"DEBUG: Pairs at end of Loop = {pairs}")
                        print(f"DEBUG: ------------------------------")

                    self.session.vars['pairs'].append(pairs)

                # define roles for human players (producer/consumer),
                for g_index, g in enumerate(self.get_groups()):   
                    # whatever number (p_index) the player is defines role
                    for p_index, p in enumerate(g.get_players()):
                        print(f"DEBUG: Normal Player: {p_index}")
                        p.participant.vars['group_color'] = Constants.red
                        print(f"DEBUG: Normal Player Color: {p.participant.vars['group_color']}")
                        p.participant.vars['group'] = g_index

                        # assigning the tokens
                        current_matchings = matching_file["matchings"][self.round_number - 1]
                        humans_matchings = current_matchings["humans"] # matchings per group for bots
                        p.participant.vars['token'] = humans_matchings[f"{p_index}"]["item"]
                        print(f"DEBUG: Normal Player Token: {p.participant.vars['token']}")
                        
                        print(f"DEBUG: Normal Player Endowment: {p.participant.payoff}")
                        p.participant.payoff += Constants.endowment
                        print(f"DEBUG: Normal Player Endowment +=: {p.participant.payoff}")

                    print(f"DEBUG: -----------------------------------------")

                # BOTS 
                self.session.vars['automated_traders'] = {}               
                # automated traders are always in 2nd half of groups
                ### ONLY CREATE BOTS IF BOT TREATMENT IS TURNED ON
                # only create bots if the bot treatment is on

                if self.session.config['automated_traders']:
                    print('starting create bots')
                    for gi in range(n_groups // 2, n_groups):
                        for pi in range(Constants.players_per_group): # pi: bot player id in group
                            print(f"DEBUG: Automated trader of group {gi}: {pi}")
                            trader = AutomatedTrader(self.session, pi + 1,
                                Constants.num_rounds, Constants.players_per_group)
                            print(f"DEBUG: Automated trader: {trader}")
                            trader.participant.vars['group_color'] = Constants.blue
                            print(f"DEBUG: Automated trader color: {trader.participant.vars['group_color']}")
                            trader.participant.vars['group'] = gi
                            print(f"DEBUG: Automated trader endowment: {trader.participant.payoff}")
                            trader.participant.payoff += Constants.endowment
                            print(f"DEBUG: Automated trader endowment +=: {trader.participant.payoff}")
                            
                            # assigning the tokens
                            current_matchings = matching_file["matchings"][self.round_number - 1]
                            bots_matchings = current_matchings["humans"] # matchings per group for bots
                            trader.participant.vars['token'] = bots_matchings[f"{pi}"]["item"]
                            print(f"DEBUG: Automated trader token: {trader.participant.vars['token']}")
                            
                            trader.dump_round_data()
                            self.session.vars['automated_traders'][(gi, pi)] = trader
                            print(f"DEBUG: -----------------------------------------")

                    for r in range(Constants.num_rounds):
                        print('starting round for bots', r + 1)
                        pairs = {}
                        groups = []
                        current_matchings = matching_file["matchings"][r]
                        bots_matchings = bots_matchings["bots"] # matchings per group for humans
                        
                        print("DEBUG: Starting bot players pairing")
                        for gi in range(n_groups // 2, n_groups): # gi: id of a group
                            # humans paired with other humans
                            for player_id_in_group in range(1, Constants.players_per_group + 1):
                                current_matching = bots_matchings[f"{player_id_in_group}"]
                                # creating the pairs for human matchings
                                if current_matching["partner_type"] == "bot":
                                    print("DEBUG: bot-bot pairing")
                                    print(f"DEBUG: Pairs at beginning of Loop = {pairs}")
                                    partner_id_in_group = current_matching["partner_id"]
                                    pairs[(gi, player_id_in_group)] = (gi, partner_id_in_group)
                                    print(f"DEBUG: Pairs during Loop = {pairs}")

                                elif current_matching["partner_type"] == "human":
                                    print("DEBUG: bot-human pairing")
                                    print(f"DEBUG: Pairs at beginning of Loop = {pairs}")
                                    partner_id_in_group = current_matching["partner_id"]
                                    pairs[(gi, player_id_in_group)] = (gi - round(n_groups/2), partner_id_in_group) # humans group are first half
                                    print(f"DEBUG: Pairs during Loop = {pairs}")
                                else:
                                    print(f"DEBUG: Undefined partner type = {current_matching['partner_type']}")                                

                        print(f"DEBUG: ----------------------------------------------")

                        # assigning pairs for bots
                        self.session.vars['pairs'].append(pairs)

            else:
                self.group_like_round(1) # to keep the players assignment to a group in rest of rounds
                
            # set number of transactions back to 0 each round
            self.fc_transactions = 0
            #print(self.session.vars['pairs'])


        else:
            with ContextSeed(42):
                if self.round_number == 1:
                    print('starting create subsession')
                    # puts players into groups of size players_per_group
                    self.group_randomly()

                    # depends on if traders are on or off
                    if self.session.config['automated_traders']:
                        n_groups = len(self.get_groups()) * 2

                    else:
                        n_groups = len(self.get_groups())

                    # create random pairings
                    # for the whole session
                    # a way to pair people given certain probabilities of
                    # getting paired within your group or within the other group
                    self.session.vars['pairs'] = []
                    for r in range(Constants.num_rounds):
                        print('starting round', r)
                        # maps traders to their trading partners
                        # (group_id, player_id) <=> (group_id, player_id)
                        # so that a player can look up who their trading partner is
                        # in this map
                        pairs = {}
                        groups = []
                        for gi in range(n_groups): # gi: id of a group
                            # create player ids in group
                            # ex: 1,2,3,4

                            print(f"DEBUG: Group {gi}")

                            #random.seed(123) # fixed initial random matching
                            #TODO: test fixed random matching
                            g = [i for i in range(Constants.players_per_group)] # g: member of a group

                            # shuffle player numbers
                            # ex: 1,3,2,4
                            
                            print(f"DEBUG: Group members = {g}")
                            random.shuffle(g)
                            print(f"DEBUG: Group members after shuffling = {g}")

                            # NOTE: self.session.config['probability_of_same_group'] times
                            # Constants.players_per_group needs to cleanly divide 2.
                            index = int(Constants.players_per_group *
                                self.session.config['probability_of_same_group'])
                            assert(index % 2 == 0)

                            # sampling probability_of_same_group % of players from g
                            # ex: 1,3
                            g_sample_homogeneous = g[:index]

                            # sampling other 1 - probability_of_same_group % of players from g
                            # ex: 2,4
                            g_sample_heterogeneous = g[index:]
                            # pairing homogeneous
                            # ex: (0,1) <=> (0,3)
                            #     (0,3) <=> (0,1)
                            for i in range(0, index, 2):
                                print(f"DEBUG: Pairs at beginning of Loop = {pairs}")
                                pairs[(gi, g_sample_homogeneous[i])] = (gi, g_sample_homogeneous[i + 1])
                                print(f"DEBUG: Pairs at middle of Loop = {pairs}")
                                pairs[(gi, g_sample_homogeneous[i + 1])] = (gi, g_sample_homogeneous[i])    
                                print(f"DEBUG: Pairs at end of Loop = {pairs}")
                                print(f"DEBUG: ------------------------------")


                            # store the heterogeneous players so they can be paired later
                            groups.append(g_sample_heterogeneous)

                        # pair traders between groups
                        # randomize trader order within each group
        #                print(groups)
                        for gi in range(n_groups // 2):
                            oi = gi + n_groups // 2 # other index, oi: group of automated traders
                            
                            random.shuffle(groups[gi])
                            (groups[oi])
                            for i in range(len(groups[gi])):
                                print(f"DEBUG: Other pair matching at beginning of Loop = {pairs}")
                                pairs[(gi, groups[gi][i])] = (oi, groups[oi][i])
                                print(f"DEBUG: Other pair matching at middle of Loop = {pairs}")
                                pairs[(oi, groups[oi][i])] = (gi, groups[gi][i])
                                print(f"DEBUG: Other pair matching at end of Loop = {pairs}")
        #               #     g = []
        #
        #
        #
        #                groups_ = copy.deepcopy(groups)
        #                # randomly select 2 different groups. then select 1 random traders
        #                # from each group. remove those traders from their respective group
        #                # lists and put them in the pairs list as a pair.
        #                # It is possible to get left with 2 traders from the same group
        #                # at the end. If this happens, scrap it and start over.
        #                # Repeat until you get a working heterogeneous pairing for each
        #                # trader.
        #                while any(groups):
        #                    indices = [i for i, gl in enumerate(groups) if len(gl) > 0] # indices of non-empty groups
        #                    if len(indices) < 2:
        #                        g = []
        #                        groups = copy.deepcopy(groups_)
        #                        continue
        #                    i0, i1 = random.sample(indices, 2)
        #                    p0 = (i0, groups[i0].pop())
        #                    p1 = (i1, groups[i1].pop())
        #                    g.append((p0, p1))
        #
        #                #g = [(i, p) for i in range(n_groups) for p in groups[i]]
        #                # num groups needs to be even (b/c one bot group per player group)
        #                # therefore len(g) is even
        #
        #                # ex: (0,4) <=> (1,8)
        #                #     (1,8) <=> (0,4)
        #                for gg in g:
        #                    pairs[gg[0]] = gg[1]
        #                    pairs[gg[1]] = gg[0]
        #
                        self.session.vars['pairs'].append(pairs)
                    # if there is only 1 group, then we can do another loop after this
                    # one and do the exact same shit, except instantiating bots
                    # instead of getting players with p.

                    # if there can be more than 1 group, we can easily just repeat the
                    # loop some number of times for the number of bot groups. And,
                    # we will also need to change the loop above to
                    # do not just 0 and 1 for g index but other numbers, and also change
                    # the method for getting your group index since looking at your
                    # color will not suffice anymore.

                    # BOTS
                    self.session.vars['automated_traders'] = {}
                    # automated traders are always in 2nd half of groups

                    ### ONLY CREATE BOTS IF BOT TREATMENT IS TURNED ON

                    # only create bots if the bot treatment is on
                    if self.session.config['automated_traders']:
                        print('starting create bots')
                        for gi in range(n_groups // 2, n_groups):
                            group_color = Constants.blue
                            print(f"DEBUG: Automated trader group: {gi}")
                            roles = [Constants.trade_good for n in range(Constants.players_per_group // 2)]
                            print(f"DEBUG: Automated trader roles: {roles}")
                            roles += [group_color for n in range(Constants.players_per_group // 2)]
                            print(f"DEBUG: Automated trader roles after +=: {roles}")
                            
                            random.shuffle(roles)
                            print(f"DEBUG: Automated trader roles after shuffling: {roles}")

                            for pi in range(Constants.players_per_group):
                                print(f"DEBUG: Automated trader of group {gi}: {pi}")
                                trader = AutomatedTrader(self.session, pi + 1,
                                    Constants.num_rounds, Constants.players_per_group)
                                print(f"DEBUG: Automated trader: {trader}")
                                trader.participant.vars['group_color'] = group_color
                                print(f"DEBUG: Automated trader color: {group_color}")
                                trader.participant.vars['group'] = gi
                                print(f"DEBUG: Automated trader endowment: {trader.participant.payoff}")
                                trader.participant.payoff += Constants.endowment
                                print(f"DEBUG: Automated trader endowment +=: {trader.participant.payoff}")
                                trader.participant.vars['token'] = roles[pi]
                                print(f"DEBUG: Automated trader token: {trader.participant.vars['token']}")
                                trader.dump_round_data()
                                self.session.vars['automated_traders'][(gi, pi)] = trader
                                print(f"DEBUG: -----------------------------------------")

                            print(f"DEBUG: ---------------------------------------------")

                    # player groups
                    print('start create players')
                    for g_index, g in enumerate(self.get_groups()):
                        group_color = Constants.red

                        # define random roles for players (producer/consumer),
                        # ensuring half are producers and half are consumers
                        # denotes half with a trade good
                        # denotes half with group color
                        print(f"DEBUG: Normal Group: {g_index}")
                        roles = [Constants.trade_good for n in range(Constants.players_per_group // 2)]
                        print(f"DEBUG: Normal Group roles: {roles}")
                        roles += [group_color for n in range(Constants.players_per_group // 2)]
                        print(f"DEBUG: Normal Group roles +=: {roles}")

                        random.shuffle(roles)
                        print(f"DEBUG: Normal Group roles after shuffle: {roles}")

                        # set each player's group color, and starting token (which
                        # determines who is going to be a producer vs consumer
                        # whatever number (p_index) the player is defines role
                        for p_index, p in enumerate(g.get_players()):
                            print(f"DEBUG: Normal Player: {p_index}")
                            p.participant.vars['group_color'] = group_color
                            print(f"DEBUG: Normal Player Color: {p.participant.vars['group_color']}")
                            p.participant.vars['group'] = g_index
                            p.participant.vars['token'] = roles[p_index]
                            print(f"DEBUG: Normal Player Token: {p.participant.vars['token']}")
                            print(f"DEBUG: Normal Player Endowment: {p.participant.payoff}")
                            p.participant.payoff += Constants.endowment
                            print(f"DEBUG: Normal Player Endowment +=: {p.participant.payoff}")

                        print(f"DEBUG: -----------------------------------------")
                    
                else:
                    self.group_like_round(1)
                    
                # set number of transactions back to 0 each round
                self.fc_transactions = 0
                #print(self.session.vars['pairs'])

class Group(BaseGroup):
    pass
    

class Player(BasePlayer):
    # For detecting mturk/online bots in this section of the game
    trading = models.LongStringField(blank=True)

    # Player Timed out
    player_timed_out = models.IntegerField(initial=0)
    my_group_id = models.IntegerField()
    my_id_in_group = models.IntegerField()
    other_group_id = models.IntegerField()
    other_id_in_group = models.IntegerField()
    role_pre = models.StringField() # 'Producer', 'Consumer'
    other_role_pre = models.StringField()
    token_color = models.StringField() # Constants.red, Constants.blue, None
    other_token_color = models.StringField()
    group_color = models.StringField() # Constants.red, Constants.blue
    other_group_color = models.StringField()
    trade_attempted = models.BooleanField(
        choices=[
            [False, 'No'],
            [True, 'Sí'],
        ],
        verbose_name = "",
        widget = widgets.RadioSelect
    )
    trade_succeeded = models.BooleanField()
    tax_paid = models.CurrencyField(initial=0)
    storage_cost_paid = models.CurrencyField(initial=0)
                
    def set_payoffs(self, round_payoff):
        self.payoff = round_payoff
