#!/bin/bash
#
# script to greedily select lists and evaluate predictions
#
###############################################################

# filename with user IDs to run list selection for
userfile="test.txt"
# number of lists to select
k=20
# graph to use for density calculations - 'colisted' or 'friendship'
graphtype="colisted"
# type of density - 'normalized' or 'average'
denstype="normalized"
# directory location of data files: .egonet, .memberships, .lists
datadir="./data/"
# directory to output selected lists to 
resdir="./"
# filename with precision, recall, F1-score
evalfile="final_results.txt"

c=0
while read u
do
    python greedySelection.py $u $k -dd $datadir -od $resdir -gt $graphtype -dens $denstype
    if [ $c -lt 1 ]; then 
        fopt="w"
    else
        fopt="a"
    fi
    python evaluateCirclePredictions.py $datadir$u".lists" $resdir$u.$graphtype.$denstype.lists -o $evalfile -fopt $fopt
    ((c++))
done <$userfile
