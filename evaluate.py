""" evaluate list predictions against ground truth
"""
import munkres 
import numpy as np
import argparse

def loadSetDict(filename):
    """ load dictionary from file with format:

        itemID val1 val2 val3\n
        itemID val2 val4 val7\n

        return dictionary with keys = itemIDs, values = set of 
            whitespace-separated items from the same line
    """
    returndict = {}
    with open(filename, 'rb') as f:
        for l in f:
            fields = l.strip().split()
            returndict[fields[0]] = set(fields[1:])

    return returndict 

def calcPrecRecF1(pred, gt):
    """ calculate the F1 between predicted set and ground truth set
    """
    overlap = float(len(pred & gt))
    if pred:
        prec = overlap/len(pred) 
    else:
        prec = 0.0
    rec = overlap/len(gt)
    if (prec + rec) != 0.0:
        return (prec, rec, (2.0 * prec * rec ) / (prec + rec))
    else:
        return (prec, rec, 0.0)

def bestMatch(pred, gtlists):
    """ find best matching between predicted and ground truth lists
    """
    ntruth = len(gtlists)
    npred = len(pred)

    # matrix of 1-F1-score costs for every list pair 
    dim = max(npred, ntruth)
    F1_matrix = np.ones([dim, dim]) 

    # fill in F1-score for all pairs 
    for i, gtlist in enumerate(gtlists):
        for j, predlist in enumerate(pred):
            F1_matrix[i,j] = 1.0 - calcPrecRecF1(predlist[1], gtlist[1])[2]

    # get optimal matching
    m = munkres.Munkres()
    matching = m.compute(F1_matrix)

    # handle case where ntruth != npred
    col_exclude = set(); row_exclude = set()
    if ntruth < npred:
        row_exclude |= set(xrange(ntruth,npred))
    elif npred < ntruth:
        col_exclude |= set(xrange(npred,ntruth))

    matching = [(c1, c2) for c1, c2 in matching if
                c1 not in row_exclude and c2 not in col_exclude]

    return matching, F1_matrix

def printEvaluation(userID, outfile, pred, gtlists, matching, scores, fopt):
    """ print precision, recall, and F1-score for each ground truth list
    """

    with open(outfile, fopt) as fout:
        if fopt == "w":
            fout.write("userID\tgtlistID\tpredID\tprec\trec\tF1\n")
        for i, idx in enumerate(matching):
            fout.write("%s\t%s\t%s\t%.3f\t%.3f\t%.3f\n" % (userID,
                        gtlists[idx[0]][0], pred[idx[1]][0], scores[i][0], 
                        scores[i][1], scores[i][2]))

def main(truthfile, predfile, outfile, fopt):
    """ evaluate circle predictions against ground truth 
    """
    print("%s" % ("".join(["-"]*70)))
    print("Ground truth: %s\nPredicted: %s" % (truthfile, predfile))
    userID = predfile.split("/")[-1].split(".")[0]
    # load ground truth, predictions
    gtlists = loadSetDict(truthfile).items()
    pred = loadSetDict(predfile).items()

    # optimal linear assignment of prediction to ground truth
    matching, F1_matrix = bestMatch(pred, gtlists) 

    # calculate precision, recall, f1score
    scores = np.zeros([len(matching), 3])
    for i, idx in enumerate(matching):
        scores[i,:] = calcPrecRecF1(pred[idx[1]][1], gtlists[idx[0]][1])

    if outfile:
        printEvaluation(userID, outfile, pred, gtlists, matching, scores, 
                        fopt)

if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("gtfile", help="ground truth file")
    parser.add_argument("predfile", help="predictions file")
    parser.add_argument("-o","--outputfile", default=None,
                        help="filename for printing output")
    parser.add_argument("-fopt", "--fileoption", choices=["a","w"],
                        help="'a' to append to file, 'w' to write new file \
                        [default='w']", default="w")
    args = parser.parse_args()

    main(args.gtfile, args.predfile, args.outputfile, args.fileoption)
