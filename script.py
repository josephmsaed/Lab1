from xmltodict import parse 
from dict2xml import dict2xml
from math import ceil
# ------------ FUNCTIONS -------------

def xml_to_dict(xmlfile):
    with open(xmlfile, 'r') as f:
        xml_str = f.read()
    f.close() 
    xml_dict = parse(xml_str)
    return xml_dict

def message_size(message, BC="SXJJ"):
    # L = 20(bits/word) * n(word) + overhead_com (depends on the communication type BC to RT, RT to BC, RT to RT)
    overhead_com = 56 if BC == message['emetteur'] or BC == message['recepteur'] else 106
    L = 20 * int(message['taille_mes']) + overhead_com
    return L
    
def transmission_delay(message, link_speed=1, BC="SXJJ"):
    """Calculates the transmission delay of message.

    Args:
        message (dictionary): the message with all its characteristics
        link_speed (int, optional): in Mbps. Defaults to 1 Mbps.
        BC (str, optional): Bus Controller or Master's name. Defaults to "SXJJ".

    Returns:
        float: the transmission delay of a message in microseconds.
    """
    L = message_size(message, BC)
    return L/link_speed

def quicksort(messages_list):
    if len(messages_list)<=1:
        return messages_list
    else:
        pivot = messages_list[0]
        inf_list = []
        sup_list = []
        for elt in messages_list[1:]:
            if elt['frequency'] < pivot['frequency']:
                inf_list.append(elt)
            else:
                sup_list.append(elt)
                
        return quicksort(sup_list) + [pivot] + quicksort(inf_list)
                     
def set_priorities_RM(messages_list):
    # the higher the frequency, the higher the priority is
    messages_list = quicksort(messages_list)
    
    prio = 1
    messages_list[0]['priority'] = prio
    for i in range(1,len(messages_list)):
        if messages_list[i]['frequency'] != messages_list[i-1]['frequency']:
                prio +=1
        messages_list[i]['priority'] = prio

    return messages_list

def max_lp_C(message, messages_list):
    max_C = 0
    for msg in messages_list:
        if message['priority'] < msg['priority']: # 1 is the highest priority
            if msg['DT'] > max_C:
                max_C = msg['DT']
                
    return max_C

def sum_hp(message, messages_list, W):
    sum = 0
    
    for msg in messages_list:
        if message['priority'] >= msg['priority']:
            sum += msg['DT'] * ceil(W / ((1/msg['frequency'])*10**6))
    return sum
    
def WCRT(message, messages_list):
    previous_W = 0
    current_W = -1
    while True:
        current_W = message['DT'] + max_lp_C(message, messages_list) + sum_hp(message, messages_list, previous_W)
        if current_W == previous_W: # current_w = WCRT
            return current_W
        else:
            previous_W = current_W

def get_shortest_period(messages_list):
    max_freq = 0
    for message in messages_list:
        if message['frequency'] > max_freq:
            max_freq = message['frequency']
    
    return (1/max_freq) * 10**6 # in microseconds

def sum_Ci(messages_list):
    sum = 0
    for message in messages_list:
        sum += message['DT']
    return sum

def schedulability_test_wcrt(message):
    if message['DBEB'] > (1/message['frequency']) * 10**6: # deadlines are violated
        message['Test'] = 'not schedulable'
    else:
        message['Test'] = 'schedulable'
    
    return message   
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
        message['DT'] =  transmission_delay(message)
        results_list.append({'name': message['nom'],
                             'frequency': float( message['frequence']),
                             'mes_size': message['taille_mes'],
                             'sender': message['emetteur'],
                             'receiver': message['recepteur'],
                             'DT' :  transmission_delay(message)  })

    print('2 - transmission delays are calculated')    
    print('--------------------------------------------')
    

    # Step 3: Performance analysis in terms of end-to end delays and access delays (d2)
    # Calculate the end-to-end delay of each message = wCRT
    # Deduce the access times to the medium (d2)
    print('3 - End to end and access delays are calculated')
    
    results_list = set_priorities_RM(results_list)
    for message in results_list:
        eed = WCRT(message, results_list)
        message['DBEB'] = eed
        message['DMAC'] = eed - message['DT']
    print('--------------------------------------------')
    
    
    # Conclude on the schedulability of each message
    # WCRT schedulabity test:
    for message in results_list:
        message = schedulability_test_wcrt(message)
    
    # Sufficient Schedulability Condition:
    Test = sum_Ci(results_list)/get_shortest_period(results_list)
    print(f"Since the value of test is: {Test} > 1, we cannot conclude on the schedulability of these set of messages using this test.")
    print('--------------------------------------------')
     
     
    # Step 4: Output xml file generation 
    results_dict = {'fichier': {'message':results_list}}
    xml = dict2xml(results_dict, wrap ="", indent ="   ")
    f = open("results.xml", "w")
    f.write(xml)
    f.close()
    
    print("4 - the output xml file is generated.")
    print('--------------------------------------------')
    
    
if __name__ =='__main__':
    main()
    


