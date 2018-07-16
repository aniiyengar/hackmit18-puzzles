
# I'm the L. Ron Hubbard of the cupboard.

import networkx as nx
import requests

base_url = 'https://gps.hackmirror.icu/api'
base_user = 'kamiquaziii_45dc2b'

target_node = 22499
safety = 3

def req_get_maze():
    url = base_url + '/map?user=' + base_user
    return requests.get(url).json()['graph']

def req_move(direction):
    url = base_url + '/move?user=%s&move=%s' % (base_user, direction)
    return requests.post(url).json()

def req_reset():
    url = base_url + '/reset?user=' + base_user
    requests.post(url)

def rowcol_to_index(row, col):
    return row * 150 + col

def path(maze, start):
    print('Recalculating path...')
    lst = nx.algorithms.shortest_paths.generic.shortest_path(maze, source=start, target=target_node)
    m = []
    for i in range(len(lst) - 1):
        diff = lst[i + 1] - lst[i]
        if diff == 1:
            m.append('right')
        elif diff == -1:
            m.append('left')
        elif diff == 150:
            m.append('down')
        elif diff == -150:
            m.append('up')
        else:
            print('wht the fuck')

    return lst, m

found = False

while not found:
    curr_pos = 0

    req_reset()
    graph = req_get_maze()

    G = nx.DiGraph()
    curr_pos = 0 # Assume at starting position

    # Generate a graph of the maze
    G.add_nodes_from(range(22500))
    for i in range(22500):
        edges = graph[i]
        for e in edges:
            G.add_edge(i, e)

    # Initial game plan
    positions, moves = path(G, curr_pos)
    positions.pop(0) # Don't need this extra info

    time_left = 600
    path_left = True

    while curr_pos != target_node:
        # Try making a move in the right direction.
        move = moves.pop(0)
        expected_dest = positions.pop(0)

        print('Time left: ' + str(time_left))
        result = req_move(move)
        time_left -= 1

        # Either we went the right way or we didn't.
        try:
            curr_pos = rowcol_to_index(result['row'], result['col'])
        except KeyError:
            print('Invalid move ass')
            break
        if curr_pos != expected_dest:
            # Fuck shit
            try:
                positions, moves = path(G, curr_pos)
                positions.pop(0)
            except:
                print('\n\nFuck. No paths left.\n\n\n==================\n\n\n')
                break

        print('== current position: ' + str(curr_pos) + ' ==')
        print

    if curr_pos == target_node:
        found = True
