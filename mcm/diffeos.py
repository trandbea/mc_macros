#! /usr/bin/env python
#-----------------------------------------------------------------------------------------
#    Script to check if all files were copied to eos and have the right file size
#    Required arguments:
#       -r   range of eos mcdb id for this model, e.g. '-r 153,156', use this if 
#            id's are consecutive and not empty ids in between
#       -l   set of mcdb ids to look at
#       -m   model name, e.g. T2tt
#    N.B. The script mounts eos in a subdirectory of the current directory called tempeos
#-----------------------------------------------------------------------------------------
import os, sys, argparse
from glob import glob
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument("-r","--range")
parser.add_argument("-l","--list")
parser.add_argument("-m","--model")
args = parser.parse_args()

idlist = []
if (args.range):
  rang = [int(i) for i in args.range.split(",")]
  if (len(rang)!=2 or rang[0]>rang[1]): sys.exit("Bad range.")
  idlist = [i for i in range(rang[0], rang[1]+1)]
elif (args.list):
  idlist = [int(i) for i in args.list.split(",")]
else:
  sys.exit("Must give a range or list of MCDB ids.")

if not args.model:
  sys.exit("Need a model name")

eospath = os.path.join(os.getcwd(), "tmpeos")
if (not os.path.exists(eospath) or len(glob(eospath+"/*"))==0):
  print "You need to mount eos into directory tmpeos"

miss = {}
xtra = {}
corr = {}
zero = {}

match = {}

eos = {}
for dbid in idlist:
  eos[dbid] = set([i.split("/").pop() for i in glob("tmpeos/cms/store/lhe/"+str(dbid)+"/*")])

datasets = glob("tmpeos/cms/store/group/phys_susy/LHE/13TeV/"+args.model+"/*")

for ds in datasets:
  print "Looking for dataset:", ds
  suspath = "tmpeos/cms/store/group/phys_susy/LHE/13TeV/"+args.model+"/"+ds.split("/").pop()+"/"
  fsus = set([i.split("/").pop() for i in glob(ds+"/*")])
  # pprint(fsus)
  found  = False
  # look through all the ids on eos, in case they are not in order or missing
  for dbid in idlist: 
    feos = eos[dbid]
    eospath = "tmpeos/cms/store/lhe/"+str(dbid)+"/"
    # pprint(eos[dbid])
    # --- found directory on eos
    if not feos.isdisjoint(fsus):
      match[ds] = dbid      
      # ---  all files exist, are they the same size?
      for ifile in (feos & fsus):
        if os.path.getsize(suspath+ifile)!=os.path.getsize(eospath+ifile):
          if (ds not in corr.keys()): corr[ds] = []
          corr[ds].append(ifile)
        elif os.path.getsize(suspath+ifile)<0.01:
          zero[ds].append(ifile)
      # --- files on eos, that are not in our folder
      if len(feos-fsus)>0:
        xtra[ds] = feos-fsus
      # --- files on eos, that are not in our folder
      if len(fsus-feos)>0: 
        miss[ds] = fsus-feos

# Summary
for ds in datasets:
  print "-"*10, ds.split("/").pop(), "-"*10
  if ds in match.keys():
    print "MCDB id =", match[ds]
    eospath = "tmpeos/cms/store/lhe/"+str(match[ds])+"/"
    suspath = "tmpeos/cms/store/group/phys_susy/LHE/13TeV/"+args.model+"/"+ds.split("/").pop()+"/"
    if (ds not in corr.keys()) and (ds not in miss.keys()) and (ds not in xtra.keys()):
      print "All files OK!."
    if (ds in corr.keys()):
      print "-- Corrupted files (i.e. file size is different):"
      flist = [eospath+ifile for ifile in corr[ds]]
      for i in flist: print i
    if (ds in miss.keys()):
      print "-- Missing files:"
      flist = [suspath+ifile for ifile in miss[ds]]
      for i in flist: print i
    if (ds in xtra.keys()):
      print "-- Extra files (on eos but not in our SUS directory):"
      flist = [eospath+ifile for ifile in xtra[ds]]
      for i in flist: print i
    if (ds in zero.keys()):
      print "-- Files with size 0 on both eos and in our SUS directory:"
      flist = [eospath+ifile for ifile in zero[ds]]
      for i in flist: print i
  else:
    print "Dataset not found on eos in the given MCDB id range or list."
