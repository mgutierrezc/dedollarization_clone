doc = """
    Matching file generator: Generator of matching files for dedollarization
    project

    Programmer: Marco Gutierrez
    Date: January 2021

    This script generates the matching files for the oTree app in JSON
    
    -input:
        -
    
    -output:
        -otree matching file
    
    ----------------------Aditional Notes------------------------------------------
    -description for init files:
        -
    """

import json
import random
import os
import string
import argparse

random.seed(123, version=2) # setting up our seed for the shuffling

def create_config_var_sets(rounds, items_matching, probability_of_same_group, num_humans, num_bots):
   """
   This function will create a list of dictionaries, where the dictionaries will contain 
   the values for the controls and for specific treatment levels

   Input:
   *Dictionary with config description: 
     description_dict = {'mtree_type': , 'name': , 'environment': , 'institution': , 'agent': }
   *Number of runs per treatment (integer)
   *Control variables dictionary
   *Treatment variables dictionary (including number_of_agents here or in controls)

   Output: 
   *mtree config file for several simulations
   """

   path = str(input(
       "\n[1] Please, input the path where you want your oTree matching file "
       "(e.g. D:/otree_project1/config/ or ./config/): \n"))

   file_name = str(input("\n[2] Input your preferred name for the matching file " 
                         "(don't write the extension):\n"))

   matchings = { # empty dict for matchings
                "name": f"{file_name}", 
                "description": "JSON matching file created for dedollarization",
                "matchings": []
                }

   for current_round in range(rounds):
       if items_matching is True:
           round_matching = {
                            "round": current_round + 1,
                            "items_matching": items_matching,
                            "humans": {}, # empty dictionary for humans matchings
                            "bots": {} # empty dictionary for bots matchings
                            }
       else:
           if current_round == 0:
               round_matching = {
                            "round": current_round + 1,
                            "items_matching": True,
                            "humans": {}, # empty dictionary for humans matchings
                            "bots": {} # empty dictionary for bots matchings
                            }
           else:
               round_matching = {
                            "round": current_round + 1,
                            "items_matching": False,
                            "humans": None, # empty dictionary for humans matchings
                            "bots": None # empty dictionary for bots matchings
                            }

       round_matching["humans"] = humans_matchings(num_humans, num_bots, round_matching["items_matching"], probability_of_same_group)
       round_matching["bots"] = bots_matchings(num_humans, num_bots, round_matching["items_matching"], round_matching["humans"])

       matchings["matchings"].append(round_matching) # storing the matching files

   #TODO: add lines for storing the generated file as a JSON

   file_path_name = path + file_name
   temp_extension = '.txt'
   # generating our temp matching file
   with open(file_path_name + temp_extension, 'a+') as target_file:
       json.dump(matchings, target_file, indent=1)

   text = open(file_path_name + temp_extension, "r") # txt file to be reformated for json
   lines = text.readlines()
   string_output = "".join(lines)

   with open(file_path_name + '.json', 'a+') as target_file:
       target_file.write(string_output)

   text.close()
   os.remove(file_path_name + temp_extension)  # erasing the tmp


def humans_matchings(number_of_humans, number_of_bots, items_matching, probability_of_same_group):
    """
    Generates matchings for human players taking without replacement
    in the format required by the matching file

    Input:
    - Number of humans (Int)
    - Number of bots (Int)

    Output:
    - Dictionary with matchings indexed from 0 to "number_of_humans"
    """
    group = 0 # humans are predefined as group 0
    other_group = 1 # humans are predefined as group 1
    group_type = "human"
    other_group_type = "bot"
    group_item = "Rojo"
    good = "Bien de Consumo"
    output = {} # dictionary with human ids in group as entries

    pairs = {}

    players_per_group = [i for i in range(number_of_humans)] # members of a human group
    bots_per_group = [i for i in range(number_of_bots)] # members of a bot group
    print(f"DEBUG: Group members = {players_per_group}")
    random.shuffle(players_per_group) # shuffling players in group
    random.shuffle(bots_per_group) # shuffling bots in group
    print(f"DEBUG: Group members after shuffling = {players_per_group}")

    # number_of_humans needs to cleanly divide 2.
    index = int(number_of_humans * probability_of_same_group)
    assert(index % 2 == 0)

    # sampling probability_of_same_group % of players from g
    # ex: 1,3
    homogeneous_sample = players_per_group[:index]

    # sampling other 1 - probability_of_same_group % of players from g
    # ex: 2,4
    heterogeneous_sample = players_per_group[index:]
    
    # # pair traders within groups
    # ex: (0,1) <=> (0,3)
    #     (0,3) <=> (0,1)
    for i in range(0, index, 2):
        print(f"DEBUG: Pairs at beginning of Loop = {pairs}")
        pairs[(group, homogeneous_sample[i])] = (group, homogeneous_sample[i + 1])
        print(f"DEBUG: Pairs at middle of Loop = {pairs}")
        pairs[(group, homogeneous_sample[i + 1])] = (group, homogeneous_sample[i])    
        print(f"DEBUG: Pairs at end of Loop = {pairs}")
        print(f"DEBUG: ------------------------------")
    
    # pair traders between groups
    for i in range(len(heterogeneous_sample)):
        print(f"DEBUG: Other pair matching at beginning of Loop = {pairs}")
        pairs[(group, heterogeneous_sample[i])] = (other_group, bots_per_group[i])
        print(f"DEBUG: Other pair matching at end of Loop = {pairs}")

    if items_matching is True:
        # item generation
        roles = [good for n in range(number_of_humans // 2)]
        print(f"DEBUG: Automated trader roles: {roles}")
        roles += [group_item for n in range(number_of_humans // 2)]
        print(f"DEBUG: Automated trader roles after +=: {roles}")    
        
        random.shuffle(roles) # item randomization

    # creating the pairs for humans
    for human in range(number_of_humans):
        print(f"DEBUG: pairs[(group, human)] = {pairs[(group, human)]}")
        partner_group = pairs[(group, human)][0]
        partner_id = pairs[(group, human)][1]
        output[f"{human}"] = {} # initializing the current output entry

        if items_matching is True:
            output[f"{human}"] = {"item": roles[human]} # assigning role

        print(f"DEBUG: output = {output}")

        # assigning partner type
        if partner_group == other_group:  # if partner group is the other group
            output[f"{human}"]["partner_type"] = other_group_type
        elif partner_group != other_group:
            output[f"{human}"]["partner_type"] = group_type
        else:
            print("DEBUG: Invalid partner group = {partner_group}")

        output[f"{human}"]["partner_id"] = partner_id # assigning partner id

    return output


def bots_matchings(number_of_humans, number_of_bots, items_matching, matchings_for_humans):
    """
    Generates matchings for human players taking without replacement
    taking in account the matchings done for humans in the format 
    required by the matching file

    Input:
    - Number of humans (Int)
    - Number of bots (Int)

    Output:
    - Dictionary with matchings indexed from 0 to "number_of_humans"
    """
    group = 1 # humans are predefined as group 0
    other_group = 0 # humans are predefined as group 1
    group_type = "bot"
    other_group_type = "human"
    group_item = "Azul"
    good = "Bien de Consumo"
    heterogeneous_pairs = {} # empty dict for storing human-bot pairings
    output = {} # dictionary with human ids in group as entries

    pairs = {}
    
    bots_per_group = [i for i in range(number_of_bots)] # members of a bot group
    print(f"DEBUG: Group members (bots) = {bots_per_group}")
    random.shuffle(bots_per_group) # shuffling bots in group
    print(f"DEBUG: Group members (bots) after shuffling = {bots_per_group}")

    # getting the human-bot matchings
    heterogeneous_sample = []
    homogeneous_sample = []
    for human_match in matchings_for_humans.keys():
        current_match = matchings_for_humans[f"{human_match}"]
        human_id = int(human_match)

        # storing them as dictionary of tuples
        if current_match["partner_type"] == "bot":
            bot_id = current_match["partner_id"]
            heterogeneous_pairs[(group, bot_id)] = (other_group, human_id)
            heterogeneous_sample.append(bot_id) # storing the bot_ids of human-bot matchings

    # storing the bot ids of homogenous matchings
    homogeneous_sample = [id for id in range(number_of_bots) if id not in heterogeneous_sample]
    random.shuffle(homogeneous_sample) # randomizing the players in the homogeneous sample

    # # pair traders within groups
    # ex: (0,1) <=> (0,3)
    #     (0,3) <=> (0,1)
    for bot in range(0, len(homogeneous_sample), 2):
        print(f"DEBUG: Pairs at beginning of Loop = {pairs}")
        pairs[(group, homogeneous_sample[bot])] = (group, homogeneous_sample[bot + 1])
        print(f"DEBUG: Pairs at middle of Loop = {pairs}")
        pairs[(group, homogeneous_sample[bot + 1])] = (group, homogeneous_sample[bot])    
        print(f"DEBUG: Pairs at end of Loop = {pairs}")
        print(f"DEBUG: ------------------------------")   

    # pair traders between groups
    pairs = {**pairs, **heterogeneous_pairs}

    if items_matching is True:
        # item generation
        roles = [good for n in range(number_of_bots // 2)]
        print(f"DEBUG: Automated trader roles: {roles}")
        roles += [group_item for n in range(number_of_bots // 2)]
        print(f"DEBUG: Automated trader roles after +=: {roles}")    
        
        random.shuffle(roles) # item randomization

    #TODO: use pairs for creating bots matchings
    for bot in range(number_of_bots):
        partner_group = pairs[(group, bot)][0]
        partner_id = pairs[(group, bot)][1]
        output[f"{bot}"] = {} # initializing the current output entry

        if items_matching is True:
            output[f"{bot}"] = {"item": roles[bot]} # assigning role

        # assigning partner type
        if partner_group == other_group:  # if partner group is the other group
            output[f"{bot}"]["partner_type"] = other_group_type
        elif partner_group != other_group:
            output[f"{bot}"]["partner_type"] = group_type
        else:
            print("DEBUG: Invalid partner group = {partner_group}")

        output[f"{bot}"]["partner_id"] = partner_id # assigning partner id

    return output