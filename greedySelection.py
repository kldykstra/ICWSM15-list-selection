""" greedily select lists by density in friendship or colisted graph 
"""
from collections import OrderedDict
import argparse
import sys
import os

def loadSetDict(filename, exclude=set()):
    """ load dictionary from file with format:

        itemID val1 val2 val3\n
        itemID val2 val4 val7\n

        return ordered dictionary with keys = itemIDs, values = set of 
        whitespace-separated items from the same line

        option to specify exclude, a set of values to remove from each line 
    """
    returndict = OrderedDict()
    with open(filename, 'rb') as f:
        for l in f:
            fields = l.strip().split()
            returndict[fields[0]] = set(fields[1:]) - exclude

    return returndict 
        
def nodemax(quality, nodes, node_maximums):
    """ Take maximum between existing node value and *quality* 

    Args:
    quality (float): measure of quality for group *nodes*
    nodes (set): node IDs to which quality applies
    node_maximums (dict): key, node ID, value, maximum quality
   
    Returns:
    node_maximums updated so that nodes have maximum value 
    """
    for n in nodes:
        node_maximums[n] = max(node_maximums[n], quality)

    return node_maximums

def calculateDensities(edgesdict, candidates, graph_type, density_type):
    """ Calculate density of each candidate list in the given graph

    Args:
    edgesdict (dict): key, value is userID, set of user IDs with shared edge
    candidates (dict): key, value is listID, set of user IDs in list
    graph_type (str): "colisted" or "friendship"

    Returns
    densities, a list of densities for each candidate list
    """

    densities = []
    for candname, nodes in candidates.items():
        # calculate density of edges within nodes
        nodeset = set(nodes)
        nodeslen = len(nodes)
        nedges = 0.0
        for n in nodes:
            nedges += len(set(edgesdict[n]) & nodeset)
        if density_type == "normalized":
            density = nedges / (nodeslen * (nodeslen-1))
        elif density_type == "average":
            density = nedges/ nodeslen
        densities.append(density)

    return densities 

def greedySelect(allnodes, qualdict, candidates, k):
    """ greedily selects k candidates based on greedily maximizing density
        summed over users

    Args:
    allnodes (set): user IDs in egonet
    qualdict (dict): key, list ID, value, density of list
    candidates (dict): key, list ID, value, set of list member IDs
    k: number of lists to select 

    Returns:
    list of k dictionaries with fields:
        'label', 'nodes', 'gain', 'quality', 'obj_func'
    """

    # initialize max list density for each user
    node_maximums = dict([(n,0) for n in allnodes])
    # store selected candidates
    bestlist = [] 
    # store current objective function value
    current_obj_func = 0

    cand_tuples = candidates.items()
    for i in xrange(k):

        print("selecting list %d" % (i+1))
        # initialize current best option
        best = {'label':None, 'nodes':None, 'gain':0, 'quality':0,
            'obj_func':0}
        bestidx = None 

        for j, graphtuple in enumerate(cand_tuples):

            label, nodes = graphtuple
            cand_quality = qualdict[j]

            # objective function value with candidate
            new_nodesmax = sum([max(cand_quality, node_maximums[n]) for n
                in nodes])
            old_nodesmax = sum([node_maximums[n] for n in nodes])
            gain = new_nodesmax - old_nodesmax 
                
            if gain > best['gain']:
                cand_obj_func = current_obj_func - old_nodesmax + \
                    new_nodesmax
                best = {'label':label, 'nodes':nodes, 'gain':gain,
                    'quality':cand_quality, 'obj_func':cand_obj_func}
                bestidx = j 

        # check for no gain in objective function
        if best["gain"] == 0:
            print("No possible gain in objective function - we're done")
            return bestlist

        # update objective function value
        current_obj_func = best['obj_func']
        # update node maximums
        node_maximums = nodemax(best['quality'], best['nodes'], 
            node_maximums)
        # delete candidate
        cand_tuples.pop(bestidx)
        qualdict.pop(bestidx)

        bestlist.append(best)

    return bestlist

def printResults(ID, outdir, best, candidates, datadir, graphtype, 
                densitytype):
    """ outputs 2 files

        1. *ID*.*graphtype*.*densitytype*.lists
            One line for each selected list, formatted:

            listID1 user1 user2 ...
            listID2 user3 user4 ...
            ...

        2. *ID*.*graphtype*.*densitytype*.stats
            Statistics about list selections (length, objective function..)
    """

    # output selected lists
    listsout = "%s%s.%s.%s.lists" % (outdir, ID, graphtype, densitytype)
    with open(listsout, "wb") as fout:
        for b in best:
            fout.write("%s\t%s\n" % (b['label'], '\t'.join(b['nodes'])))

    # output stats about list selection
    statsout = "%s%s.%s.%s.stats" % (outdir, ID, graphtype, densitytype)
    with open(statsout, "wb") as fout:
        fout.write("%s\t%s\t%s\t%s\t%s\n" % ("listID", "len", 
            "objfunc", "quality", "gain"))
        for b in best:
            fout.write("%s\t%d\t%.4f\t%.4f\t%.4f\n" % (
                b['label'], len(b['nodes']), b['obj_func'], 
                b['quality'], b['gain']))

def main(userID, k, datadir, outdir, graphtype, densitytype):
    """ select k lists

    INPUT
    userID (str): user ID to perform list selection for
    k (int): number of lists to select
    datadir (str): directory location of data files
    outdir (str): directory location for output .lists and .stats files
    graphtype (str): 'colisted' or 'friendship'
    densitytype (str): 'average' or 'normalized' for avg. degree or 
        normalized density
    """

    # check for required files
    egofile = "%s%s.egonet" % (datadir, userID)
    listfile = "%s%s.lists" % (datadir, userID)
    membershipfile = "%s%s.memberships" % (datadir, userID)
    required_files = [egofile, listfile, membershipfile]
    for f in required_files:
        if not os.path.isfile(f):
            sys.exit("could not find required file %s" % f)

    # load egonet 
    egonet = loadSetDict(egofile)
    egousers = set(egonet.keys())
    # load ground truth lists
    listdict = loadSetDict(listfile) 
    gtlists = set(listdict.keys())
    # load user list memberships (excluding ground truth lists)
    memshipdict = loadSetDict(membershipfile, exclude = gtlists)

    # dictionary with key, list ID, value, set of list member IDs
    listmems = OrderedDict() 
    for u, memships in memshipdict.items():
        for l in memships:
            listmems.setdefault(l, set()).add(u)

    if graphtype == "friendship":
        # edges in friendship graph
        edgedict = egonet
    elif graphtype == "colisted":
        # edges in colisted graph
        edgedict = {} 
        for u, memships in memshipdict.items():
            for l in memships:
                edgedict[u] = edgedict.setdefault(u, set()).union(
                                                  listmems[l] - set([u]))

    # keep lists with 3 or more members as candidates
    candidates = {}
    for l, lmems in listmems.items():
        if len(lmems) < 3:
            del(listmems[l])
    candidates.update(listmems)

    print("(%s) %d users in egonet, %d candidate lists" % (userID, 
           len(egousers), len(candidates)))

    # calculate density of list candidates 
    qualdict = calculateDensities(edgedict, candidates, graphtype,
                                  densitytype) 
    # greedily select top k candidates for density
    best = greedySelect(egousers, qualdict, candidates, k)
    # output results
    printResults(userID, outdir, best, candidates, datadir, graphtype,
                 densitytype)


if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("userID", help="ID of egonet user for which to \
                        perform list selection")
    parser.add_argument("k", help="number of lists to select",
                        type = int)
    parser.add_argument("-dd","--datadir", help = "location of .egonet, \
                        .lists, and .memberships files")
    parser.add_argument("-od","--outdir",
                        help = "location to output selected lists")
    parser.add_argument("-gt", "--graphtype", choices=["friendship", 
                        "colisted"], help="graph type for density \
                         calculations; choose from 'friendship',\
                         'colisted'")
    parser.add_argument("-dens", "--densitytype", choices=["average",
                        "normalized"], help="type of density to \
                        calculate, chooces from 'average' (average \
                        degree) and 'normalized'")
    args = parser.parse_args()

    main(args.userID, args.k, args.datadir, args.outdir, args.graphtype,
         args.densitytype)
