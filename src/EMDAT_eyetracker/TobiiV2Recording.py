"""
UBC Eye Movement Data Analysis Toolkit (EMDAT), Version 3
Created on 2015-08-15

Class to read Tobii data (exported with Tobii Studio version 1x and 2x). See sample data in the "sampledata" folder.

Authors: Mike Wu (creator), Sebastien Lalle.
Institution: The University of British Columbia.
"""

from EMDAT_core.Recording import *
from EMDAT_core.data_structures import Datapoint, Fixation, Saccade, Event
from EMDAT_core.utils import *
import csv
import params


class TobiiV2Recording(Recording):
    def read_all_data(self, all_file):
        """Returns a list of "Datapoint"s read from an "All-Data" file.

        Args:
            all_file:A string containing the name of the 'All-Data.tsv' file output by the Tobii software.

        Returns:
            a list of "Datapoint"s
        """
        all_data = []
        with open(all_file, 'r') as f:
            # for _ in xrange(params.ALLDATAHEADERLINES + params.NUMBEROFEXTRAHEADERLINES - 1):
            #     next(f)
            reader = csv.DictReader(f, delimiter="\t")
            last_pupil_left = None
            last_pupil_right = None
            last_time = -1

            for row in reader:
                # if not row["Number"]:  # ignore invalid data point
                #     continue
                pupil_left = None  # cast_float(row["PupilLeft"], -1)
                pupil_right = None  # cast_float(row["PupilRight"], -1)
                distance_left = None  # cast_float(row["DistanceLeft"], -1)
                distance_right = None  # cast_float(row["DistanceRight"], -1)
                timestamp = int(float(row["RecordingTimestamp"]))  # cast_int(row["Timestamp"])
                data = {"timestamp": timestamp,
                        "pupilsize": get_pupil_size(pupil_left, pupil_right),
                        "pupilvelocity": get_pupil_velocity(last_pupil_left, last_pupil_right, pupil_left, pupil_right,
                                                            (timestamp - last_time)),
                        "distance": get_distance(distance_left, distance_right),
                        "is_valid": True,  # cast_int(row["ValidityRight"]) < 2 or cast_int(row["ValidityLeft"]) < 2,
                        "is_valid_blink": None,
                        # cast_int(row["ValidityRight"]) < 2 and cast_int(row["ValidityLeft"]) < 2,
                        "stimuliname": None,  # row["StimuliName"],
                        "fixationindex": None,  # cast_int(row["FixationIndex"]),
                        "gazepointxleft": float(row["avg_x"])}
                all_data.append(Datapoint(data))
                last_pupil_left = pupil_left
                last_pupil_right = pupil_right
                last_time = timestamp

        return all_data

    def read_fixation_data(self, fixation_file):
        """Returns a list of "Fixation"s read from an "Fixation-Data" file.

        Args:
            fixation_file: A string containing the name of the 'Fixation-Data.tsv' file output by the Tobii software.

        Returns:
            a list of "Fixation"s
        """

        all_fixation = []
        with open(fixation_file, 'r') as f:
            # for _ in xrange(params.FIXATIONHEADERLINES - 1):
            #     next(f)
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                data = {"fixationindex": cast_int(row["Unnamed: 0"]),
                        "timestamp": int(float(row["starttime"])),
                        "fixationduration": int(float(row["duration"])),
                        "fixationpointx": int(float(row["endx"])),
                        "fixationpointy": int(float(row["endy"]))}
                all_fixation.append(Fixation(data, self.media_offset))

        return all_fixation

    def read_event_data(self, event_file):
        """Returns a list of "Event"s read from an "Event-Data" file.

        Args:
            event_file: A string containing the name of the 'Event-Data.tsv' file output by the Tobii software.

        Returns:
            a list of "Event"s
        """

        all_event = []
        with open(event_file, 'r') as f:
            for _ in xrange(params.EVENTSHEADERLINES - 1):
                next(f)
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                data = {"timestamp": cast_int(row["Timestamp"]),
                        "event": row["Event"],
                        "event_key": cast_int(row["EventKey"])}
                if data["event"] == "LeftMouseClick" or data["event"] == "RightMouseClick":
                    data.update({"x_coord": cast_int(row["Data1"]), "y_coord": cast_int(row["Data2"])})
                elif data["event"] == "KeyPress":
                    data.update({"key_code": cast_int(row["Data1"]), "key_name": row["Descriptor"]})
                elif data["event"] == "LogData":
                    data.update({"description": row["Data1"]})
                all_event.append(Event(data, self.media_offset))

        return all_event

    # def read_saccade_data(self, saccade_file):
    #     """ no saccade in data exported from Tobii Studio V1-V2
    #     """
    #     pass

    def read_saccade_data(self, saccade_file):
        """Returns a list of "Saccade"s read from the data file file.

        Args:
            saccade_file: A string containing the name of the data file output by the Tobii software.

        Returns:
            a list of "Saccade"s
        """

        all_saccade = []
        with open(saccade_file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            in_saccade = False
            in_fixation = False
            last_gaze_coord = (0, 0, 0)  # timestamp X Y
            saccade_vect = []
            saccade_duration = 0
            current_index = 0

            nb_invalid_temp = 0
            nb_valid_sample = 0
            nb_sample = 0
            last_valid = False

            for row in reader:
                #                if row["MediaName"] != 'ScreenRec' or not row["EyeTrackerTimestamp"]:
                if row["MediaName"] != 'Screen Recordings (1)' or not row[
                    "EyeTrackerTimestamp"]:  # ignore non-recording data point
                    continue

                if in_fixation:
                    if row["GazeEventType"] == "Fixation":
                        nb_invalid_temp = 0
                    elif row["GazeEventType"] == "Saccade":  # new saccade
                        in_fixation = False
                        in_saccade = True
                        current_index = row["SaccadeIndex"]
                        saccade_vect = [last_gaze_coord]
                        nb_valid_sample = 0

                        # add current sample
                        if (EMDAT_core.utils.cast_int(row["ValidityLeft"]) < 2 or EMDAT_core.utils.cast_int(
                                row["ValidityRight"]) < 2) and row["GazePointX (ADCSpx)"] and row[
                            "GazePointY (ADCSpx)"]:  # ignore data point with no valid data
                            saccade_vect.append([EMDAT_core.utils.cast_int(row["RecordingTimestamp"]),
                                                 EMDAT_core.utils.cast_int(row["GazePointX (ADCSpx)"]),
                                                 EMDAT_core.utils.cast_int(row["GazePointY (ADCSpx)"])])
                            nb_valid_sample += 1

                        if last_valid:
                            nb_valid_sample += 1

                        nb_sample = 2 + nb_invalid_temp  # current gaze sample + last gaze sample of the previous fixation + eventually all unclasified gaze samples in between
                        nb_invalid_temp = 0
                    else:  # unclassified gaze samples
                        nb_invalid_temp += 1

                elif in_saccade:
                    if row["GazeEventType"] == "Fixation":
                        in_fixation = True
                        in_saccade = False

                        # end of last saccade
                        if (EMDAT_core.utils.cast_int(row["ValidityLeft"]) < 2 or EMDAT_core.utils.cast_int(
                                row["ValidityRight"]) < 2) and row["GazePointX (ADCSpx)"] and row[
                            "GazePointY (ADCSpx)"]:  # valid last datapoint
                            saccade_vect.append([EMDAT_core.utils.cast_int(row["RecordingTimestamp"]),
                                                 EMDAT_core.utils.cast_int(row["GazePointX (ADCSpx)"]),
                                                 EMDAT_core.utils.cast_int(row["GazePointY (ADCSpx)"])])
                            nb_valid_sample += 1
                        elif (row["FixationPointX (MCSpx)"] and row["FixationPointY (MCSpx)"]):  # if gaze sample not valid, try to use fixation data instead
                            saccade_vect.append([EMDAT_core.utils.cast_int(row["RecordingTimestamp"]),
                                                 EMDAT_core.utils.cast_int(row["FixationPointX (MCSpx)"]),
                                                 EMDAT_core.utils.cast_int(row["FixationPointY (MCSpx)"])])
                            nb_valid_sample += 1
                        nb_sample += 1

                        rate_valid_sample = float(nb_valid_sample) / nb_sample
                        if rate_valid_sample >= params.VALID_SAMPLES_PROP_SACCADE:  # if saccade quality is above the threshold
                            saccade_duration = EMDAT_core.utils.cast_int(row["RecordingTimestamp"]) - \
                                               saccade_vect[0][0]
                            dist = EMDAT_core.Recording.get_saccade_distance(saccade_vect)
                            accel = -1  # Recording.get_saccade_acceleration(saccade_vect)
                            speed = float(dist) / EMDAT_core.utils.cast_int(saccade_duration)
                            data = {"saccadeindex": EMDAT_core.utils.cast_int(current_index),
                                    "timestamp": saccade_vect[0][0],
                                    "saccadeduration": EMDAT_core.utils.cast_int(saccade_duration),
                                    "saccadestartpointx": saccade_vect[0][1],
                                    "saccadestartpointy": saccade_vect[0][2],
                                    "saccadeendpointx": saccade_vect[-1][1],
                                    "saccadeendpointy": saccade_vect[-1][2],
                                    "saccadedistance": dist,
                                    "saccadespeed": speed,
                                    "saccadeacceleration": accel,
                                    "saccadequality": rate_valid_sample
                                    }
                            all_saccade.append(Saccade(data, self.media_offset))
                            nb_valid_sample = 0
                            nb_sample = 0

                    elif row["GazeEventType"] == "Saccade":
                        if (EMDAT_core.utils.cast_int(row["ValidityLeft"]) < 2 or EMDAT_core.utils.cast_int(
                                row["ValidityRight"]) < 2) and row["GazePointX (ADCSpx)"] and row[
                            "GazePointY (ADCSpx)"]:  # ignore data point with no valid data
                            saccade_vect.append([EMDAT_core.utils.cast_int(row["RecordingTimestamp"]),
                                                 EMDAT_core.utils.cast_int(row["GazePointX (ADCSpx)"]),
                                                 EMDAT_core.utils.cast_int(row["GazePointY (ADCSpx)"])])
                            nb_valid_sample += 1
                        nb_sample += 1
                    else:  # unclassified gaze samples
                        nb_sample += 1
                    nb_invalid_temp = 0

                else:  # wait for the first fixation
                    if row["GazeEventType"] == "Fixation":
                        in_fixation = True

                if row["GazePointX (ADCSpx)"] and row["GazePointY (ADCSpx)"]:
                    last_gaze_coord = (EMDAT_core.utils.cast_int(row["RecordingTimestamp"]),
                                       EMDAT_core.utils.cast_int(row["GazePointX (ADCSpx)"]),
                                       EMDAT_core.utils.cast_int(row["GazePointY (ADCSpx)"]))
                    last_valid = (EMDAT_core.utils.cast_int(row["ValidityLeft"]) < 2 or EMDAT_core.utils.cast_int(
                        row["ValidityRight"]) < 2)
                elif row["GazeEventType"] == "Fixation" and row["FixationPointX (MCSpx)"] and row[
                    "FixationPointY (MCSpx)"]:  # if last sample not valid, at least check if valid data about the fixation
                    last_gaze_coord = (EMDAT_core.utils.cast_int(row["RecordingTimestamp"]),
                                       EMDAT_core.utils.cast_int(row["FixationPointX (MCSpx)"]),
                                       EMDAT_core.utils.cast_int(row["FixationPointY (MCSpx)"]))
                    last_valid = True

        return all_saccade
