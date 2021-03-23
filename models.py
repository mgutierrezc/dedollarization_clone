from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
import copy
import json
from .project_logger import get_logger
from .automated_trader import AutomatedTrader

logger = get_logger('models.py')

class ContextSeed:
    """
    context manager to ensure sample draws are
    shared among different agents
    """
    def __init__(self, seed):
        pass
        # self.seed = seed #DEBUG
    
    def __enter__(self):
        pass
        # random.seed(self.seed) #DEBUG
    
    def __exit__(self, *_):
        pass
        # random.seed(random.randint(0, 100)) #DEBUG


class Constants(BaseConstants):
    name_in_url = 'dedollarization'
    instructions_button = 'dedollarization/Instructions_Button.html'
    instructions_template = 'dedollarization/Instructions.html'
    contact_template = 'dedollarization/Contactenos.html'
    players_per_group = 8
    number_of_bots = 20
    # num_rounds = 115 # for production run
    num_rounds = 30 # for demo run
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

    logger.debug("-> Entering Subsession")

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
                logger.debug(f"70: create subsession")

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
                    logger.debug(f"88: starting round for humans {r + 1}")
                    # maps traders to their trading partners
                    # (group_id, player_id) <=> (group_id, player_id)
                    # so that a player can look up who their trading partner is
                    # in this map
                    # 'r' is an index for the dictionaries within matching_file["matchings"]
                    pairs = {}
                    groups = []
                    current_matchings = matching_file["matchings"][r]
                    humans_matchings = current_matchings["humans"] # matchings per group for humans
                    logger.debug("97: Starting human players pairing")
                    for gi in range(round(n_groups/2)): # gi: id of a group
                        # humans paired with other humans
                        for player_id_in_group in range(Constants.players_per_group):
                            current_matching = humans_matchings[f"{player_id_in_group}"]
                            # creating the pairs for human matchings
                            if current_matching["partner_type"] == "human":
                                logger.debug("104: human pairing")
                                logger.info(f"Pairs at beginning of Loop = {pairs}")
                                partner_id_in_group = current_matching["partner_id"]
                                pairs[(gi, player_id_in_group)] = (gi, partner_id_in_group)
                                logger.info(f"Pairs during Loop = {pairs}")

                            elif current_matching["partner_type"] == "bot":
                                logger.debug("111: bot pairing")
                                logger.info(f"Pairs at beginning of Loop = {pairs}")
                                partner_id_in_group = current_matching["partner_id"]
                                pairs[(gi, player_id_in_group)] = (gi + round(n_groups/2), partner_id_in_group) # bots group are other half
                                logger.info(f"Pairs during Loop = {pairs}")
                            else:
                                logger.info(f"Undefined partner type = {current_matching['partner_type']}")

                        logger.info(f"Pairs at end of Loop = {pairs}")
                        logger.info(f"------------------------------")

                    self.session.vars['pairs'].append(pairs)

                # define roles for human players (producer/consumer),
                logger.debug(f"125: define roles for human players (producer/consumer)")
                for g_index, g in enumerate(self.get_groups()):   
                    # whatever number (p_index) the player is defines role
                    for p_index, p in enumerate(g.get_players()):
                        logger.info(f"Normal Player: {p_index}")
                        p.participant.vars['group_color'] = Constants.red
                        logger.info(f"Normal Player Color: {p.participant.vars['group_color']}")
                        p.participant.vars['group'] = g_index

                        # assigning the tokens
                        current_matchings = matching_file["matchings"][self.round_number - 1]
                        humans_matchings = current_matchings["humans"] # matchings per group for bots
                        logger.info(f"p_index = {p_index}")
                        p.participant.vars['token'] = humans_matchings[f"{p_index}"]["item"]
                        logger.info(f"Normal Player Token: {p.participant.vars['token']}")
                        
                        logger.info(f"Normal Player Endowment: {p.participant.payoff}")
                        p.participant.payoff += Constants.endowment
                        logger.info(f"Normal Player Endowment +=: {p.participant.payoff}")

                    logger.info(f"-----------------------------------------")

                # BOTS 
                #TODO: add them an extra round for storing last round switches
                self.session.vars['automated_traders'] = {}    # {round_#: {(group_id, bot_id): {"token":, "group_color": , 
                                                               # "payoff": }}}

                # automated traders are always in 2nd half of groups
                ### ONLY CREATE BOTS IF BOT TREATMENT IS TURNED ON
                # only create bots if the bot treatment is on

                if self.session.config['automated_traders']:
                    logger.debug('153: starting create bots')
                    for round_num in range(1, Constants.num_rounds + 2):
                        automated_traders = self.session.vars['automated_traders'][f"round_{round_num}"] = {}                        
                        for gi in range(n_groups // 2, n_groups):
                            for pi in range(Constants.number_of_bots): # pi: bot player id in group
                                logger.info(f"Automated trader of group {gi}: {pi}")
                                automated_traders[(gi, pi)] = {}
                                automated_trader = automated_traders[(gi, pi)]
                                #trader = AutomatedTrader(self.session, pi + 1,
                                #    Constants.num_rounds, Constants.players_per_group)
                                logger.info(f"Automated trader: {automated_trader}")
                                automated_trader['group_color'] = Constants.blue
                                logger.info(f"Automated trader color: {automated_trader['group_color']}")
                                automated_trader['group'] = gi
                                logger.info(f"Automated trader endowment: {automated_trader['payoff']}")
                                automated_trader['payoff'] += Constants.endowment
                                logger.info(f"Automated trader endowment +=: {automated_trader['payoff']}")
                                
                                # assigning the tokens
                                if round_num < Constants.num_rounds + 1:
                                    current_matchings = matching_file["matchings"][self.round_number - 1]
                                    bots_matchings = current_matchings["bots"] # matchings per group for bots
                                    logger.info(f"pi (bot index) = {pi}")
                                    automated_trader['token'] = bots_matchings[f"{pi}"]["item"]
                                    logger.info(f"Automated trader token: {automated_trader['token']}")
                                    
                                    logger.info(f"-----------------------------------------")


                    for r in range(Constants.num_rounds):
                        print('179: starting round for bots', r + 1)
                        pairs = {}
                        groups = []
                        logger.info(f"182: matching_file[matchings][r] = {matching_file['matchings'][r]} ")
                        current_matchings = matching_file["matchings"][r]
                        bots_matchings = current_matchings["bots"] # matchings per group for humans
                        
                        logger.debug("186: Starting bot players pairing")
                        for gi in range(n_groups // 2, n_groups): # gi: id of a group
                            # humans paired with other humans
                            for player_id_in_group in range(Constants.number_of_bots):
                                current_matching = bots_matchings[f"{player_id_in_group}"]
                                # creating the pairs for human matchings
                                if current_matching["partner_type"] == "bot":
                                    logger.debug("bot-bot pairing")
                                    logger.info(f"Pairs at beginning of Loop = {pairs}")
                                    partner_id_in_group = current_matching["partner_id"]
                                    pairs[(gi, player_id_in_group)] = (gi, partner_id_in_group)
                                    logger.info(f"Pairs during Loop = {pairs}")

                                elif current_matching["partner_type"] == "human":
                                    logger.debug("bot-human pairing")
                                    logger.info(f"Pairs at beginning of Loop = {pairs}")
                                    partner_id_in_group = current_matching["partner_id"]
                                    pairs[(gi, player_id_in_group)] = (gi - round(n_groups/2), partner_id_in_group) # humans group are first half
                                    logger.info(f"Pairs during Loop = {pairs}")
                                else:
                                    logger.info(f"Undefined partner type = {current_matching['partner_type']}")                                

                        logger.info(f"----------------------------------------------")

                        # assigning pairs for bots
                        self.session.vars['pairs'][r] = {**self.session.vars['pairs'][r], **pairs}
                        logger.info(f"212: total pairs round {r} = {self.session.vars['pairs']}")

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
                    logger.debug("241: create random pairings")
                    for r in range(Constants.num_rounds):
                        logger.info(f"starting round {r}")
                        # maps traders to their trading partners
                        # (group_id, player_id) <=> (group_id, player_id)
                        # so that a player can look up who their trading partner is
                        # in this map
                        pairs = {}
                        groups = []
                        logger.debug("250: mapping traders to their trading partners")
                        for gi in range(n_groups): # gi: id of a group
                            # create player ids in group
                            # ex: 1,2,3,4

                            logger.info(f"Group {gi}")

                            g = [i for i in range(Constants.players_per_group)] # g: member of a group

                            # shuffle player numbers
                            # ex: 1,3,2,4
                            
                            logger.info(f"Group members = {g}")
                            random.shuffle(g)
                            logger.info(f"Group members after shuffling = {g}")

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
                            logger.debug("284: pairing homogeneous")
                            for i in range(0, index, 2):
                                logger.info(f"Pairs at beginning of Loop = {pairs}")
                                pairs[(gi, g_sample_homogeneous[i])] = (gi, g_sample_homogeneous[i + 1])
                                logger.info(f"Pairs at middle of Loop = {pairs}")
                                pairs[(gi, g_sample_homogeneous[i + 1])] = (gi, g_sample_homogeneous[i])    
                                logger.info(f"Pairs at end of Loop = {pairs}")
                                logger.info(f"------------------------------")


                            # store the heterogeneous players so they can be paired later
                            groups.append(g_sample_heterogeneous)

                        # pair traders between groups
                        # randomize trader order within each group
                        logger.debug("299: pairing heterogeneous")
                        for gi in range(n_groups // 2):
                            oi = gi + n_groups // 2 # other index, oi: group of automated traders
                            
                            random.shuffle(groups[gi])
                            (groups[oi])
                            for i in range(len(groups[gi])):
                                logger.info(f"Other pair matching at beginning of Loop = {pairs}")
                                pairs[(gi, groups[gi][i])] = (oi, groups[oi][i])
                                logger.info(f"Other pair matching at middle of Loop = {pairs}")
                                pairs[(oi, groups[oi][i])] = (gi, groups[gi][i])
                                logger.info(f"Other pair matching at end of Loop = {pairs}")
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
                        logger.info(f"pairs = {self.session.vars['pairs']}")
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
                    logger.debug("358: creating bots")
                    # automated traders are always in 2nd half of groups

                    ### ONLY CREATE BOTS IF BOT TREATMENT IS TURNED ON

                    # only create bots if the bot treatment is on
                    if self.session.config['automated_traders']:
                        print('starting create bots')
                        for gi in range(n_groups // 2, n_groups):
                            group_color = Constants.blue
                            logger.info(f"Automated trader group: {gi}")
                            roles = [Constants.trade_good for n in range(Constants.players_per_group // 2)]
                            logger.info(f"Automated trader roles: {roles}")
                            roles += [group_color for n in range(Constants.players_per_group // 2)]
                            logger.info(f"Automated trader roles after +=: {roles}")
                            
                            random.shuffle(roles)
                            logger.info(f"Automated trader roles after shuffling: {roles}")

                            for pi in range(Constants.players_per_group):
                                
                                logger.info(f"Automated trader of group {gi}: {pi}")
                                automated_traders[(gi, pi)] = {}
                                automated_trader = automated_traders[(gi, pi)]
                                logger.info(f"Automated trader: {automated_trader}")
                                automated_trader['group_color'] = Constants.blue
                                logger.info(f"Automated trader color: {automated_trader['group_color']}")
                                automated_trader['group'] = gi
                                logger.info(f"Automated trader endowment: {automated_trader['payoff']}")
                                automated_trader['payoff'] += Constants.endowment
                                logger.info(f"Automated trader endowment +=: {automated_trader['payoff']}")
        
                                # assigning the tokens
                                automated_trader['token'] = roles[pi]
                                logger.info(f"Automated trader token: {automated_trader['token']}")
                                logger.info(f"-----------------------------------------")

                            logger.info(f"---------------------------------------------")

                    # player groups
                    logger.debug("398: create player groups")
                    for g_index, g in enumerate(self.get_groups()):
                        group_color = Constants.red

                        # define random roles for players (producer/consumer),
                        # ensuring half are producers and half are consumers
                        # denotes half with a trade good
                        # denotes half with group color
                        logger.info(f"Normal Group: {g_index}")
                        roles = [Constants.trade_good for n in range(Constants.players_per_group // 2)]
                        logger.info(f"Normal Group roles: {roles}")
                        roles += [group_color for n in range(Constants.players_per_group // 2)]
                        logger.info(f"Normal Group roles +=: {roles}")

                        random.shuffle(roles)
                        logger.info(f"Normal Group roles after shuffle: {roles}")

                        # set each player's group color, and starting token (which
                        # determines who is going to be a producer vs consumer
                        # whatever number (p_index) the player is defines role
                        for p_index, p in enumerate(g.get_players()):
                            logger.info(f"Normal Player: {p_index}")
                            p.participant.vars['group_color'] = group_color
                            logger.info(f"Normal Player Color: {p.participant.vars['group_color']}")
                            p.participant.vars['group'] = g_index
                            p.participant.vars['token'] = roles[p_index]
                            logger.info(f"Normal Player Token: {p.participant.vars['token']}")
                            logger.info(f"Normal Player Endowment: {p.participant.payoff}")
                            p.participant.payoff += Constants.endowment
                            logger.info(f"Normal Player Endowment +=: {p.participant.payoff}")

                        logger.info(f"-----------------------------------------")
                    
                else:
                    self.group_like_round(1)
                    
                # set number of transactions back to 0 each round
                self.fc_transactions = 0
                #print(self.session.vars['pairs'])

    logger.debug("<- Exiting Subsession")

class Group(BaseGroup):
    logger.debug("-> Entering Subsession")
    logger.debug("<- Exiting Subsession")
    

class Player(BasePlayer):
    logger.debug("-> Entering Player")

    # For detecting mturk/online bots in this section of the game
    trading = models.LongStringField(blank=True)

    # Player Timed out
    player_timed_out = models.IntegerField(initial=0)
    total_timeouts = models.IntegerField(initial=0)
    total_discounts = models.CurrencyField(initial=0)
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

    logger.debug("<- Exiting Player")