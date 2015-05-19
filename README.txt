Code for greedily selecting lists by density and evaluating selections 
against ground truth lists in a user's ego network. More information can be found in:

Covering the Egonet: A Crowdsourcing Approach to Social Circle Discovery 
on Twitter. K. Dykstra, J. Lijffijt, A. Gionis (2015) International 
Conference on Web and Social Media.

A toy example session is given for user "test" in runall.sh. For every ego
user the code expects the following files:

*egoID*.lists: lists that the user subscribes to or owns (ground truth)
*egoID*.memberships: list memberships for each user in the egonet
*egoID*.egonet: friendships between users in the egonet 

Toy examples with expected formatting are in ./data/

Due to Twitter's restrictions on data sharing we cannot post the whole 
dataset. The Twitter user IDs used are given in the file "users.txt" and 
membership, friends, and list information can be collected by querying 
the Twitter API, using e.g. python-twitter.

Implementation of the Hungarian/Kuhn-Munkres algorithm (munkres.py) 
written by Brian Clapper.
