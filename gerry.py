
import requests
import scipy.stats
import random

base_user = raw_input('Username: ')

data = requests.get("https://gerry.hackmirror.icu/u/%s/voters.json" % base_user).json()['voters_by_block']

def print_soln(soln):
    for i in range(10):
        print('  '.join(str(n).zfill(2) for n in soln[10*i:10*(i+1)]))

def inspect_solution(soln):
    # A solution is a 100-long array wtih each element 0 <= x <= D - 1.
    # First check if the solution is valid.
    if len(soln) != 100:
        return {
            'valid': False,
            'reason': 'Bad length'
        }

    for i in range(20):
        num = sum([1 for x in soln if x == i])
        if not (1 <= num):
            return {
                'valid': False,
                'reason': '%s has size %s' % (i, num)
            }

    for i in range(20):
        # Run DFS to find if district is contiguous
        fringe = []
        visited = []
        start = soln.index(i)
        fringe.append(start)

        popped = 0

        while len(fringe):
            n = fringe.pop()
            if n not in visited:
                popped += 1
                visited.append(n)
                if n == 0:
                    children = [1, 10]
                elif n == 9:
                    children = [8, 19]
                elif n == 90:
                    children = [80, 91]
                elif n == 99:
                    children = [98, 89]
                elif n % 10 == 0:
                    children = [n - 10, n + 10, n + 1]
                elif n % 10 == 9:
                    children = [n - 10, n + 10, n - 1]
                elif n < 9:
                    children = [n - 1, n + 1, n + 10]
                elif n > 90:
                    children = [n - 1, n + 1, n - 10]
                else:
                    children = [n - 1, n + 1, n - 10, n + 10]
                for c in children:
                    if soln[c] == i and c not in visited:
                        fringe.append(c)

        if popped != sum([1 for x in soln if x == i]):
            return {
                'valid': False,
                'reason': 'District %s not contiguous' % str(i)
            }

    # Found that the map is valid. Now find metrics
    da = data['party_A']
    db = data['party_B']

    def district_voters(i):
        a = sum([da[c] for c in range(100) if soln[c] == i])
        b = sum([db[c] for c in range(100) if soln[c] == i])
        return a, b

    # District population imbalance
    totals = [district_voters(i)[0] + district_voters(i)[1] for i in range(20)]
    mean = sum(totals) / len(totals)

    dpi = sum([(totals[i] - mean)**2 for i in range(20)])

    # Expected efficiency gap
    #
    # First we have to simulate an election between two voter bases in a district.
    #
    # If A ~ N(0.6a, 0.24a) and B ~ N(0.6b, 0.24b) the distribution of
    # Z = A - B ~ N(0.6(a-b), 0.0576(a^2 + b^2)). The probability Z > 0 means
    # the standard normal is above -2.5 * (a - b) / sqrt(a^2 + b^2).
    def simulate(a, b):
        return scipy.stats.norm(0, 1).cdf(2.5 * (a - b) / (a**2 + b**2)**0.5)

    wasted_a = 0
    wasted_b = 0
    for i in range(20):
        # Given the expected wins of each district, calculate the wasted votes
        a, b = district_voters(i)
        # A's expected vote count: 0.6a + 0.4b
        # B's expected vote count: 0.4a + 0.6b
        ea = 0.6*a + 0.4*b
        eb = 0.4*a + 0.6*b

        p_a = simulate(a,b)
        p_b = 1 - p_a
        a_waste = p_a * (ea - eb - 1) + (1 - p_a) * (ea)
        b_waste = p_b * (eb - ea - 1) + (1 - p_b) * (eb)

        wasted_a += a_waste
        wasted_b += b_waste

    effgap = (wasted_a - wasted_b) / sum(totals)
    exp_a = sum(simulate(*district_voters(i)) for i in range(20))

    return {
        'valid': True,
        'stats': {
            'expected_a': exp_a,
            'pop_imbalance': dpi,
            'efficiency_gap': effgap,
            'total_a': sum(da[i] for i in range(len(da))),
            'total_b': sum(db[i] for i in range(len(da)))
        }
    }

s = []
for i in range(20):
    s = s + ([i]*5)

def eq(x, y):
    return False not in [x[i] - y[i] == 0 for i in range(len(x))]

# Genetic algorithm pls

found_mutations = []

def gen_children(soln, num, dist):
    result = []
    for i in range(num):
        found = False
        while not found:
            copy = soln[:]

            for _ in range(dist):
                # Pick a random district to mutate
                district = random.randint(0,19)

                # In that district, pick a random grid square surrounding it
                places = [i for i in range(100) if copy[i] == district]
                neighbors = [i for i in range(100) if True in
                    [(abs(i - place) == 1 or abs(i - place) == 10) and (i not in places) for place in places]
                ]
                if not len(places):
                    break
                if len(neighbors):
                    to_add = random.choice(neighbors)

                # Also pick some random grid in the places
                to_remove = random.choice(places)

                should_add = should_remove = True

                if should_remove:
                    # Get neighbors of should remove to see which district to make
                    ns = [i for i in range(100) if (abs(i - to_remove) in (1, 10))]
                    possible_switches = list(set(copy[x] for x in ns if copy[x] != district))
                    if len(possible_switches):
                        should_remove_to = random.choice(possible_switches)
                        copy[to_remove] = should_remove_to

                if len(neighbors) and should_add:
                    copy[to_add] = district

            # This will work sometimes
            r = inspect_solution(copy)
            if r['valid'] and not eq(soln, copy):
                if True not in [eq(copy, m) for m in found_mutations]:
                    # Lucked out
                    result.append(copy)
                    found_mutations.append(copy)
                    found = True

    return result

def gen_score(soln):
    r = inspect_solution(soln)
    ex = r['stats']['expected_a']
    gap = r['stats']['efficiency_gap']
    imb = r['stats']['pop_imbalance']
    if ex > 9:
        ex = 9
    if gap > -0.046:
        gap = -0.046
    if imb < 63e10:
        imb = 63e10

    return ex * 1.5 + gap * 70 - imb / 3e11

best = float('-inf')
best_child = None
fringe = [s]
found = False
while not found:
    soln = fringe.pop(0)
    children = gen_children(soln, 5, 2)
    if best_child:
        children = children + [best_child]
    scores = [gen_score(c) for c in children]
    contender = max(scores)
    best_child = children[scores.index(contender)]
    if best < contender:
        r = inspect_solution(best_child[:])
        best = contender
        print('New best score: '+ str(contender))
        print('ExpA:           ' + str(r['stats']['expected_a']))
        print('PopImbalance:   ' + str(r['stats']['pop_imbalance']))
        print('EfficiencyGap:  ' + str(r['stats']['efficiency_gap']))
        print_soln(best_child)
        print
        print

        if r['stats']['expected_a'] > 9 and r['stats']['pop_imbalance'] < 63e10 and r['stats']['efficiency_gap'] > -0.046:
            found = True
            print('Found an answer!\n\n')
    fringe = [best_child]

r = []
for i in range(20):
    places = [ix for ix in range(100) if best_child[ix] == i]
    r.append(places)

print(r)
