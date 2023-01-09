import xmltodict 



# ------------ FUNCTIONS -------------

def xml_to_list(xmlfile):
    """_summary_

    Args:
        xmlfile (_type_): _description_

    Returns:
        _type_: _description_
    """
    with open(xmlfile, 'r') as f:
        xml_str = f.read()
    f.close() 
    xml_dict = xmltodict.parse(xml_str)
    return xml_dict['fichier']['message']

def transmission_delay(message, link_speed=1):
    """Calculates the transmission delay of message.

    Args:
        message (Dictionary): the message with all its characteristics
        link_speed (int, optional): in Mbps. Defaults to 1 Mbps.

    Returns:
        float: The transmission delay of a message in microseconds.
    """
    
    # L = 20(bits/word) * n(word) + overhead_com (depends on the communication type BC to RT, RT to BC, RT to RT)
    
    BC = 'SXJJ' # the Master
    overhead_com = 56 if BC == message['emetteur'] or BC == message['recepteur'] else 106
    L = 20 * int(message['taille_mes']) + overhead_com
    return L/link_speed
# ------------------------------------

results_dict = {}


# Step 1 Interpretation of input data
xml_list = xml_to_list('xmlB1-periodique.xml')
print(f'The number of messages in the xml file is: {len(xml_list)}')
print(f'Each message has the following characteristics: \n{xml_list[0].keys()}')
print('--------------------------------------------')
for message in xml_list:
    print(message)
print('--------------------------------------------')


# Step 2: Computation of the transmission delay (d3) (L/B)
# Compute the total size of each message
# Deduce the transmission delay of each message by taking into account a link speed of 1Mbps
print('Transmission delays:')

for message in xml_list:
    name = message['nom']
    if name not in results_dict.keys():
        results_dict[name] = {'trans_delay': transmission_delay(message)}
    else:
        results_dict[name]['trans_delay'] = transmission_delay(message)
    
print(results_dict)
print('--------------------------------------------')

# Step 3: Performance analysis in terms of end-to end delays and access delays (d2)
# Calculate the end-to-end delay of each message
# Deduce the access times to the medium (d2)
# Conclude on the schedulability of each message

# Step 4: Output xml file generation 
    


