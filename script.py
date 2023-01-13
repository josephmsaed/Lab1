from xmltodict import parse 
from dict2xml import dict2xml
from math import ceil

# ------------ FUNCTIONS -------------
def xml_to_dict(xmlfile):
    """Using the parse function of xmltodict library, this function opens an xml file
    and store its content in a dictionary.

    Args:
        xmlfile (string): relative path to the xmlfile to be read.

    Returns:
        dictionary: contains the xml file's data.
    """
    with open(xmlfile, 'r') as f:
        xml_str = f.read()
    f.close() 
    xml_dict = parse(xml_str)
    return xml_dict


def message_length(message, BC="SXJJ"):
    """Computes the total message length in bits taking into account the overhead length and if it is sent to many receivers

    Args:
        message (dictionary): must contain the message's characteristics in its keys like: 'emeteur', 'recepteur' and 'taille_mes'.
        BC (str, optional): the Master's name. Defaults to "SXJJ".

    Returns:
        int: total length of the message in bits
    """    
    # L = 20(bits/word) * n(word) + overhead_com (depends on the communication type BC to RT, RT to BC, RT to RT)
    sender = message['emetteur']
    receiver = message['recepteur']
    
    overhead_com = 56 if (sender == BC) or (receiver == BC) else 106
    L = 20 * int(message['taille_mes']) + overhead_com
        
    return L


def get_components(messages_list):
    """Stores all the names of the components (masters and slaves) in a list

    Args:
        messages_list (list): list of dictionaries containing all the messages and their characteristics.

    Returns:
        list: list of strings containing components' names.
    """
    components_list = []
    for message in messages_list:
        if message['emetteur'] not in components_list:
            components_list.append(message['emetteur'])
        elif message['recepteur'] not in components_list:
            components_list.append(message['recepteur'])
    return components_list
            
    
def transmission_delay(message, link_speed=1, BC="SXJJ"):
    """Calculates the transmission delay of message.

    Args:
        message (dictionary): the message with all its characteristics
        link_speed (int, optional): bandwidth in Mbps. Defaults to 1 Mbps.
        BC (str, optional): Bus Controller or Master's name. Defaults to "SXJJ".

    Returns:
        float: the transmission delay of a message in microseconds.
    """
    L = message_length(message, BC)
    return L/link_speed


def quicksort(messages_list):
    """ Recursive function. Sorts the list of dictionaries in the descending order of the key 'frequence'.

    Args:
        messages_list (list): list of dictionaries containing all the messages and their characteristics.

    Returns:
        list: a sorted list of dictionaries.
    """
    if len(messages_list)<=1:
        return messages_list
    else:
        pivot = messages_list[0]
        inf_list = []
        sup_list = []
        for elt in messages_list[1:]:
            if elt['frequence'] < pivot['frequence']:
                inf_list.append(elt)
            else:
                sup_list.append(elt)
                
        return quicksort(sup_list) + [pivot] + quicksort(inf_list)
   
                     
def set_priorities_RM(messages_list):
    """Adds a key to each element of the input list signaling the priority of each message
    based on Rate Monotonic Scheduling. With 1 being the highest priority.

    Args:
        messages_list (list): list of dictionaries containing all the messages and their characteristics.
                            its elements must have the key 'frequence'.

    Returns:
        list: list of dictionaries containing a new key 'priority'.
    """
    # the higher the frequency, the higher the priority is
    messages_list = quicksort(messages_list)
    
    prio = 1
    messages_list[0]['priority'] = prio
    for i in range(1,len(messages_list)):
        if messages_list[i]['frequence'] != messages_list[i-1]['frequence']:
                prio +=1
        messages_list[i]['priority'] = prio

    return messages_list

def max_lp_C(message, messages_list):
    """Computes the max C of the messages in messages_list that have lower priority than message.
    Used in the WCRT formula.

    Args:
        message (dictionary): the message for which WCRT will be calculated. Must have the following keys: 'priority' and 'DT'.
        messages_list (list): list of dictionaries containing all the messages and their characteristics.

    Returns:
        float: the max WCET of the lower priority messages in bits.
    """
    max_C = 0
    for msg in messages_list:
        if message['priority'] < msg['priority']: # 1 is the highest priority
            if msg['DT'] > max_C:
                max_C = msg['DT']
                
    return max_C


def sum_hp(message, messages_list, W):
    """Compute the a sum using the transmission delay and period of messages from messages_list,
    which have higher or equal priority than message. Used in the WCRT formula.

    Args:
        message (dicionary): the message for which WCRT will be calculated. 
                            Must have the following keys: 'priority', 'frequence' and 'DT'.
        messages_list (list): list of dictionaries containing all the messages and their characteristics.
        W (float): the W calculated in a previous iteration.

    Returns:
        float: sum to be used in the WCRT calculation formula
    """
    sum = 0
    for msg in messages_list:
        if message['priority'] >= msg['priority'] and message['nom'] != msg['nom']:
            sum += msg['DT'] * ceil(W / ((1/msg['frequence'])*10**6))
    return sum
    
def WCRT(message, messages_list):
    """WCRT theorem for Rate Monotonic. It calculates the maximum end to end delay bound of a message.
    Uses 'max_lp_C' and 'sum_hp' functions.
    
    Args:
        message (dictionary): the message in question. 
        messages_list (list): list of dictionaries containing all the messages and their characteristics.

    Returns:
        float: the end to end delay in microseconds
    """
    previous_W = 0
    current_W = -1
    while True:
        current_W = message['DT'] + max_lp_C(message, messages_list) + sum_hp(message, messages_list, previous_W)
        if current_W == previous_W: # current_w = WCRT
            return current_W
        else:
            previous_W = current_W


def get_shortest_period(messages_list):
    """Retrieves the shortest period from the messages_list.

    Args:
        messages_list (list): list of dictionaries containing all the messages and their characteristics.
                            Must have the following key: 'frequence'.

    Returns:
        float: the shortest period found in the input list.
    """
    max_freq = 0
    for message in messages_list:
        if message['frequence'] > max_freq:
            max_freq = message['frequence']
    
    return (1/max_freq) * 10**6 # in microseconds


def sum_Ci(messages_list):
    """Computes the sum of all the messages' transmission delays.

    Args:
        messages_list (list): list of dictionaries containing all the messages and their characteristics.
                            Must have the following key: 'DT'.

    Returns:
        float: the sum of the transmission delays in microseconds.
    """
    sum = 0
    for message in messages_list:
        sum += message['DT']
    return sum


def schedulability_test_wcrt(message):
    """Adds the key 'Test' to the message dictionary to signal if its schedulable or not based on 
    the WCRT theorem for Rate Monotonic.

    Args:
        message (dictionary): the message in question. Must contain the following keys: 'DBEB' and 'frequence'

    Returns:
        dictionary: the input dictionary with one added key 'Test'.
    """
    if message['DBEB'] > (1/message['frequence']) * 10**6: # deadlines are violated
        message['Test'] = 'not schedulable'
    else:
        message['Test'] = 'schedulable'
    
    return message


def write_xmlfile(results, filename):
    """Writes the data included in the results list in an xml file filename.

    Args:
        results (list): list of messages containing all of its original and new characteristics.
        filename (string): the name of the xml file to be written.
    """
    for msg in results:
        if 'priority' in msg.keys():
            del msg['priority']
    
    results_dict = {'fichier': {'message':results}}
    xml = dict2xml(results_dict, wrap ="", indent ="   ")
    f = open(filename + ".xml", "w")
    f.write(xml)
    f.close()

# -------------------------------------------------------
# -------------------------------------------------------

def main():
    
    results_list = []
    
    # Step 1 Interpretation of input data
    xml_list = xml_to_dict('xmlB1-periodique.xml')['fichier']['message']
    
    print('--------------------------------------------')
    print(f'The number of messages in the xml file is: {len(xml_list)}')
    print(f'1 - Each message has the following characteristics: \n{xml_list[0].keys()}')
    print('--------------------------------------------')
    for message in xml_list:
        print(message)
    print('--------------------------------------------')


    # Step 2: Computation of the transmission delay (DT) (L/B)
    # Compute the total size of each message
    # Deduce the transmission delay of each message by taking into account a link speed of 1Mbps
    for message in xml_list:
        results_list.append({'nom': message['nom'],
                             'frequence': float( message['frequence']),
                             'taille_mes': message['taille_mes'],
                             'emetteur': message['emetteur'],
                             'recepteur': message['recepteur'],
                             'DT' :  transmission_delay(message)  })

    print('2 - transmission delays are calculated')    
    print('--------------------------------------------')
    

    # Step 3: Performance analysis in terms of end-to end delays and access delays (d2)
    # Calculate the end-to-end delay of each message = wCRT
    # Deduce the access times to the medium (d2)
    results_list = set_priorities_RM(results_list)
    for message in results_list:
        eed = WCRT(message, results_list)
        message['DBEB'] = eed
        message['DMAC'] = eed - message['DT'] # E.E.D = d2 + d3
    
    print('3 - End to end and access delays are calculated')
    print('--------------------------------------------')
    

    # Conclude on the schedulability of each message
    # WCRT schedulabity test:
    for message in results_list:
        message = schedulability_test_wcrt(message)
    
    print('Individual schedulability tests were made')
    print('--------------------------------------------')
    
    # Sufficient Schedulability Condition:
    Test = sum_Ci(results_list)/get_shortest_period(results_list)
    print(f"Since the value of test is: {Test} > 1, we cannot conclude on the schedulability of these set of messages using this test.")
    print('--------------------------------------------')
     
     
    # Step 4: Output xml file generation 
    
    write_xmlfile(results_list, 'results')
    
    
    print("4 - the output xml file is generated.")
    print('--------------------------------------------')
    
    
    
if __name__ =='__main__':
    main()
    


