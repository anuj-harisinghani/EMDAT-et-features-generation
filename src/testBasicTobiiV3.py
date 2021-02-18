"""
UBC Eye Movement Data Analysis Toolkit (EMDAT), Version 3
Created on 2015-08-15

Sample code to run EMDAT for a given experiment.

@author: Sebastien Lalle (creator)
Institution: The University of British Columbia.
"""

from BasicParticipant import * 
from EMDAT_core.Participant import export_features_all, write_features_tsv
from EMDAT_core.ValidityProcessing import output_Validity_info_Segments, output_percent_discarded, output_Validity_info_Participants
from EMDAT_core.utils import log_to_file


import csv
#reset output log
open(params.CANARY_OUTPUT_LOG, 'w').close()

# extract user list from the pupilbaseline file
ul = []
with open(params.RPSFILE) as tsvfile:
    tsvreader = csv.reader(tsvfile, delimiter="\t")
    next(tsvreader, None)  # skip the headers
    for line in tsvreader:
        ul.append(line[0])

log_to_file("Total number of participants read from pupil_baseline file: " + str(len(ul)) + "\n")

#remove participants that EMDAT complains have no samples
p_no_samples =['EL-114', 'EO-028','HI-045','EA-046','ET-171']

for p in p_no_samples:
    ul.remove(p)
    log_to_file("Participant "+p+" removed as it had no samples!\n")

log_to_file("Total number of participants removed due to lack of samples: " + str(len(p_no_samples)) + "\n")


#ul = [7, 19, 26, 36, 38, 52, 57]

#to debug with few participants
# ul = ul[1:4]
# ul = ['EA-149','EA-175']


# user ids
uids = ul
# time offsets from start of the recording
#alogoffset = [0, 0, 0]

# Read participants
ps = read_participants_Basic(user_list = ul, pids = uids, datadir = params.EYELOGDATAFOLDER,
                             prune_length = None,
                             aoifile = None,
                             require_valid_segs = False,
                             auto_partition_low_quality_segments = False,
                             rpsfile = params.RPSFILE )

#if params.DEBUG or params.VERBOSE == "VERBOSE":
#    # explore_validation_threshold_segments(ps, auto_partition_low_quality_segments = False)
#    output_Validity_info_Segments(ps, auto_partition_low_quality_segments_flag = False, validity_method = 3)
#    output_percent_discarded(ps, './outputfolder/smi_disc.csv')
#    output_Validity_info_Segments(ps, auto_partition_low_quality_segments_flag = False, validity_method = 2,
#                              threshold_gaps_list = [100, 200, 250, 300], output_file = "./outputfolder/tobiiv3_Seg_val.csv")
#    output_Validity_info_Participants(ps, include_restored_samples = True, auto_partition_low_quality_segments_flag = False)


# WRITE features to file
#if params.VERBOSE != "QUIET":#
#    print#
#    print "Exporting:\n--General:", params.featurelist
#write_features_tsv(ps, params.EYELOGDATAFOLDER+'/outputfolder/EMDAT_features.tsv', featurelist=params.featurelist, id_prefix=True)

aoi_feat_names = (map(lambda x:x, params.aoigeneralfeat))
if params.VERBOSE != "QUIET":
     print()
     print("Exporting features:\n--General:", params.featurelist, "\n--AOI:", aoi_feat_names)#, "\n--Sequences:", params.aoisequencefeat)
     
write_features_tsv(ps, params.EYELOGDATAFOLDER+'/EMDAT/EMDAT_features.tsv',featurelist = params.featurelist,
            aoifeaturelabels = params.aoifeaturelist, id_prefix = True)

