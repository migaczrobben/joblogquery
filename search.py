# ---------------------------- #
# Import requisite information #
# ---------------------------- #

try:
    # Allows for operations on time (to get run-time of jobs)
    import datetime

    # Needed to read log files quickly
    import os

    # Used to format strings
    import re

    # Allows program to interpret variables like $UUFSCELL and run commands
    import subprocess

    # Collects arguments and exits safely if errors are encountered
    import sys

    # Additional time operations
    import time
except:
    print("Failed to load one or more required modules; are you using Python 2.7.3?")
    raise SystemExit





# ---------------- #
# Global variables #
# ---------------- #

# Set variables to default state
options = {
    "show":             5,
                        # Number of results to display
    "location":         "/uufs/$UUFSCELL/sys/var/slurm/log/slurm.job.log",
                        # Location of the log file
    "user":             False,
                        # User ID of user
    "node":             False,
                        # Node on which the job ran
    "group":            False,
                        # Name of user's group
    "job":              False,
                        # Job ID
    "partition":        False,
                        # Partition name
    "state":            False,
                        # Job state
    "runtime":          False,
                        # Time for which the program ran (done in minutes for compatibility)
    "timelimit":        False,
                        # Time limit set by user
    "timepercentage":   False,
                        # Time used over time requested, as a percentage
    "nnode":            False,
                        # The number of nodes used in the job
    "nprocess":         False,
                        # The number of processes used
    "display":          "simple",
                        # How the information appears (as output)
    "location":         ""
                        # The location to search for information
}
# Make a list for the results of the program
results = []
# Keep the number of errors for output formatting
number_of_errors = 0
# Keep errors until the end of the program; may be unnecessary in certain "display" options
error_text = ""
# Number each time the main program runs for error reporting
block = 0
# Determine whether to show the help menu
use_strict = 0
# Create a list to store formatted nodes (may need to be used multiple times)
formatted_list = []
# Store values for string replacement in nodes
values = {}
# Keep track of the number of requested arguments
requested = 0
# Keep track of the arguments that are found to be correct
correct = []
# Allow real names to be found if specified (slows down program)
real_name = 0
# Prevent column titles from being shown more than once on display "neat"
show_titles = 0
# Allow multiple locations to be searched by checking whether multiple have been entered
mod_locations = 0
# Provide "debounce" for printing values
db = []





# --------- #
# Main body #
# --------- #

# Read the log file (magic)
def line(name, size = 8192):
    # Open the log file to read information
    with open(name) as all_lines:
        # Set the offset for file reading (don't read everything again)
        offset = 0
        part = None
        all_lines.seek(0, os.SEEK_END)
        file_size = remaining_size = all_lines.tell()
        # Repeat until the beginning of the file is reached
        while remaining_size > 0:
            # Determine whether the next "group" of information should be the rest of the file
            offset = min(file_size, offset + size)
            # Navigate the file
            all_lines.seek(file_size - offset)
            # Get the current "block" of lines
            text = all_lines.read(min(remaining_size, size))
            remaining_size -= size
            lines = text.split("\n")
            # Ensure full lines are given (not parts of them)
            if part is not None:
                if text[-1] is not "\n":
                    lines[-1] += part
                else:
                    yield part
            part = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if len(lines[index]):
                    yield lines[index]
        if part is not None:
            yield part

# Get content after "=" in Slurm variables
def simple_value(here):
    try:
        answer = here.split("=")[1]
        # Remove everything in parentheses
        detail = answer.find("(")
        if detail != -1:
            # "Crop" the string, assuming only one "(" character
            answer = answer[:detail]
        return(answer)
    except:
        # Provide for errors in formatting string
        return("N/A")

# Display results as output
def print_all(origin):
    global block
    global number_of_errors
    global error_text
    global show_titles
    # Prevent more than one error from being found in finding a real name
    debounce = 0
    # Prevent more than one error in printing lines
    debounce_failure = 0
    # Get all elements in the list (lines in "results")
    for item in range(0, len(origin)):
        if not isinstance(origin[item], list):
            try:
                everything = origin[item] = origin[item].split(" ")
                for element in range(0, len(everything)):
                    if options["display"] == "simple" or options["display"] == "neat":
                        everything[element] = simple_value(everything[element])
                # Configure and display when the display mode is set to "simple" or "neat"
                if options["display"] == "simple" or options["display"] == "neat":
                    # job user group job_name job_state partition time_limit start_time end_time node_list node_count process_count working_directory
                    ran_on = " ran on "
                    spaces = "          "
                    get_name = ""
                    try:
                        if real_name == 1:
                            get_name = " (" + subprocess.check_output(["finger", everything[1]]).split("\n")[0].split("Name: ")[1] + ")"
                        else:
                            get_name = ""
                    except:
                        if debounce == 0:
                            number_of_errors += 1
                            error_text += "Block " + str(block) + ": Failed to find user's real name. Are you using the Python 2.7.3 module?\n"
                            debounce = 1
                        get_name = ""
                        pass
                    if everything[9] == "":
                        ran_on = " did not run on any nodes "
                    else:
                        ran_on = " ran on " + everything[9] + " "
                    n_node = " node" if everything[10] == "1" else " nodes"
                    n_process = " process" if everything[11] == "1" else " processes"

                    # Format the elapsed time (run-time) of the program
                    elapsed_time_datetime = datetime.datetime.strptime(everything[8].replace("T", " "), "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(everything[7].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                    total_seconds = elapsed_time_datetime.total_seconds()
                    elapsed_d = datetime.timedelta(seconds = total_seconds)
                    elapsed_time = str(elapsed_d.days) + "d " + str(time.strftime("%H:%M:%S", time.gmtime(elapsed_d.seconds)))

                    # Format the requested time (done to preserve hh:mm:ss instead of h:mm:ss for formatting)
                    time_limit_datetime = datetime.timedelta(minutes = int(everything[6]))
                    requested_seconds = time_limit_datetime.total_seconds()
                    time_limit_f = str(time_limit_datetime.days) + "d " + str(time.strftime("%H:%M:%S", time.gmtime(time_limit_datetime.seconds)))
                    time_limit = everything[6]

                    # Calculate the percentage of the requested time that the run-time represents
                    percentage = "{0:.2f}".format(total_seconds / requested_seconds * 100)

                    if options["display"] == "simple":
                        # Print each line found in the results
                        print((str(item + 1) + ".").ljust(10) + "Job " + everything[0] + ran_on + "(" + everything[10] + n_node + ", " + everything[11] + n_process + ") and has state \"" + everything[4].lower() + "\"\n" + spaces + "Submitted by " + everything[1] + get_name + " of group \"" + everything[2] + "\" to partition \"" + everything[5] + "\"\n" + spaces + "Started at " + everything[7].replace("T", " ") + " and finished at " + everything[8].replace("T", " ") + "\n" + spaces + "Run-time: " + elapsed_time + " (" + time_limit_f + " requested; " + percentage + "% used)")
                        # Print a new line for formatting
                        print("")
                    elif options["display"] == "neat":
                        # Show a header for each column, but only once
                        if show_titles == 0:
                            print("Job|User|Group|Name|State|Partition|Time Limit (min)|Start Time|End Time|Node List|Number of Nodes|Number of Processes|Directory|Real Name|Run-time|Time Limit (formatted)|Percentage of Time Used")
                            show_titles = 1
                        # Store all information for formatting
                        build = ""
                        # Store only the final, formatted information
                        final = ""
                        for obj in range(0, len(everything)):
                            # Remove the empty element included at the end of the list
                            if obj != len(everything) - 1:
                                if obj == 7 or obj == 8:
                                    # Format time in a human-readable manner
                                    everything[obj] = everything[obj].replace("T", " ")
                                # Add a pipe character for separation
                                build += everything[obj] + "|"
                        # Remove the string formatting on the user's real name (done earlier for ease of use)
                        build += get_name.replace("(", "").replace(")", "").replace(" ", "", 1) + "|"
                        # Display time information for each object
                        build += elapsed_time + "|" + time_limit_f + "|" + percentage + "|"
                        split_build = build.split("|")
                        for e in range(0, len(split_build)):
                            # Don't add a pipe character to the last
                            if e != len(split_build) - 1:
                                if split_build[e] != "":
                                    final += split_build[e] + "|"
                                else:
                                    final += "N/A|"
                        print(final[:len(final) - 1])
                elif options["display"] == "format":
                    # Display when the display mode is set to "format"
                    print(everything[0] + "|" + everything[1] + "|" + everything[2] + "|" + everything[3] + "|" + everything[4] + "|" + everything[5] + "|" + everything[6] + "|" + everything[7] + "|" + everything[8] + "|" + everything[9] + "|" + everything[10] + "|" + everything[11] + "|" + everything[12])
            except:
                if debounce_failure == 0:
                    number_of_errors += 1
                    error_text += "Block " + str(block) + ": Failed to print one or more lines. This may be related to formatting in the log file itself.\n"
                    debounce_failure = 1

# Determine whether user input matches a node list
def return_match(user_input):
    global formatted_list
    # Store formatted_list, as it is overwritten in formatting user_input
    inside = formatted_list
    # Set default value
    is_match = False
    # Keep track of current value
    tracker = True
    # Formatted version of user's nodes
    for node in format_nodes(user_input):
        # Use zeros to pad node number as it appears in inside
        if str(node).zfill(3) in inside:
            tracker = tracker and True
        else:
            tracker = tracker and False
    # Reset formatted_list to its value from the log file
    formatted_list = inside
    # Return True or False
    return(tracker)

# Format the user's node list with boolean valuesosprey
def replace(match):
    global values
    return values[match.group(0)]

# Sort the results list
def sort_res(from_list):
    global db
    for item in from_list:
        if not item in db:
            print(item.split(" ")[8])
        db.append(item)
    # job user group job_name job_state partition time_limit start_time end_time node_list node_count process_count working_directory

# Format a list of nodes (as a string, not a list)
def format_nodes(node_list):
    # Add a place to store formatted nodes
    global formatted_list
    global correct
    # See whether "node_list" is a string or a list
    if isinstance(node_list, list):
        global values
        values = {}
        origin = node_list[0]
        user_input = node_list[0].replace("(", "").replace(")", "").split(" ")
        for item in user_input:
            if item != "and" and item != "or" and item != "not":
                values[item] = str(return_match(item))
        for key, obj in values.iteritems():
            origin = origin.replace(key, obj)
        if str(eval(origin)) == "True" and not "node" in correct:
            correct.append("node")
    # If it's a string, format it!
    else:
        formatted_list = []
        # Remove prefix and square brackets from the node list
        node_list = re.sub("[a-z]", "", node_list).replace("[", "").replace("]", "").split(",")
        # Get each element in the list created by splitting at commas
        for node in node_list:
            hyphen = node.find("-")
            # Get a range of values if a hyphen is present
            if hyphen != -1:
                # Store all the values temporarily (in case they need to be changed)
                first = int(node[:hyphen])
                second = int(node[hyphen + 1:])
                f_first = 0
                f_second = 0
                # Switch the range if it is given as large-small instead of small-large
                if first > second:
                    f_second = second
                    f_first = first
                    second = f_first
                    first = f_second
                for n in range(first, second + 1):
                    # Format the node as a string with leading zeros
                    formatted_list.append(str(n).zfill(3))
            else:
                # If there is no hyphen, it can be assumed the list item is a single node
                formatted_list.append(node)
        return(formatted_list)

# Format text fields like group and user
def format_text_fields(text, user_in, type_of):
    global correct
    global requested
    global values

    # Format the text from the line
    additional = text.find("(")
    if additional != -1:
        text = text[:additional]

    values = {}
    # Save the user's input for later formatting
    origin = user_in
    user_in = user_in.replace("(", "").replace(")", "").split(" ")
    for item in user_in:
        # Don't do anything to keywords used for logic manipulation
        if item != "and" and item != "or" and item != "not":
            # Do a simple matching operation if no complex logic is found
            if item.find("<") == -1 and item.find(">") == -1:
                # Remove "=" if it is not accompanied with "<" or ">" (in case a user wants a job "==12345" instead of a job "12345")
                item = item.replace("=", "")
                if item == text:
                    values[item] = "True"
                else:
                    values[item] = "False"
            elif item.find("<") != -1 or item.find(">") != -1:
                # Evaluate any logic given by the user
                values[item] = str(eval(text + item))
    # Replace all keys in the dictionary with their values
    for key, obj in values.iteritems():
        origin = origin.replace(key, obj)
    # Get a final result, using the original text and all replaced values
    current_value = str(eval(origin))
    # Prevent duplicates from interfering with values that have already been checked
    if current_value == "True" and not type_of in correct:
        correct.append(type_of)

# Iterate through each line in the log file
def run():
    global correct
    global error_text
    global number_of_errors
    global results
    global requested
    # Things to do for each line
    for part in line(options["location"]):
        try:
            # Reset "correct" for all lines
            correct = []
            # See whether the nodes are found in the line
            if options["node"] != False:
                # Format and understand the node list
                format_nodes(part.split(" ")[9].split("=")[1])
                # Send the user's nodes as a list to avoid errors
                format_nodes([options["node"]])
            if options["user"] != False:
                # Format the user from the line and user
                format_text_fields(part.split(" ")[1].split("=")[1], options["user"], "user")
            if options["group"] != False:
                # Format text from both sources of group names
                format_text_fields(part.split(" ")[2].split("=")[1], options["group"], "group")
            if options["partition"] != False:
                # Format the partition information from both sources
                format_text_fields(part.split(" ")[5].split("=")[1], options["partition"], "partition")
            if options["state"] != False:
                # Format the job state
                format_text_fields(part.split(" ")[4].split("=")[1].lower(), options["state"].lower(), "state")
            if options["job"] != False:
                # Format the job number
                format_text_fields(part.split(" ")[0].split("=")[1], options["job"], "job")
            if options["timelimit"] != False:
                # Format the time limit
                format_text_fields(part.split(" ")[6].split("=")[1], options["timelimit"], "timelimit")
            if options["nnode"] != False:
                # Format the number of nodes
                format_text_fields(part.split(" ")[10].split("=")[1], options["nnode"], "nnode")
            if options["nprocess"] != False:
                # Format the number of processes
                format_text_fields(part.split(" ")[11].split("=")[1], options["nprocess"], "nprocess")
            if options["runtime"] != False:
                # Format the run-time
                start = datetime.datetime.strptime(part.split(" ")[7].split("=")[1].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                end = datetime.datetime.strptime(part.split(" ")[8].split("=")[1].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                time_difference = (end - start).total_seconds() / 60
                format_text_fields(str(time_difference), options["runtime"], "runtime")
            if options["timepercentage"] != False:
                # Format the time percentage
                start_2 = datetime.datetime.strptime(part.split(" ")[7].split("=")[1].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                end_2 = datetime.datetime.strptime(part.split(" ")[8].split("=")[1].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                r_time = (end_2 - start_2).total_seconds() / 60
                t_limit = part.split(" ")[6].split("=")[1]
                perc = float(r_time) / float(t_limit) * 100
                format_text_fields(str(perc), options["timepercentage"], "timepercentage")
            # Add line to "results" if all requested variables are found
            if requested == len(correct) and (options["show"] == "all" or len(results) < int(options["show"])):
                if not part in results:
                    results.append(part)
            # If the user hasn't requested all results and enough have been found, print them
            elif options["show"] != "all":
                if len(results) == int(options["show"]):
                    if mod_locations == 0:
                        print_all(sort_res(results))
                        # Reset results in case other blocks need to be executed
                        results = []
                    # Stop trying to find matches and let the program continue
                    return None
        # If reading fails on a line, skip it (this may need to be updated; errors are currently given in individual functions (format_nodes, format_text_fields))
        except:
            pass

    # After the file has been read, print everything if a specific number of results was not requested
    if options["show"] == "all":
        if mod_locations == 0:
            print_all(sort_rest(results))
            # Reset results for other blocks
            results = []
            # Stop executing "run" and allow the program to continue
            return None

    # If not enough results have been found, display the current results accompanied by an error message
    if mod_locations == 0:
        if str(options["show"]).lower() != "all":
            global block
            if len(results) < int(options["show"]):
                # Print whatever has been found
                print_all(sort_res(results))
                number_of_errors += 1
                # Adjust the output text to account for the number of results
                was_were = "was" if len(results) == 1 else "were"
                error_text += "Block " + str(block) + ": Too few results. Of " + str(options["show"]) + " requested (\"show\"), " + str(len(results)) + " " + was_were + " found.\n"
        # Remove the results to allow the program to be executed in blocks
        results = []

#
#
#
# Will need to be formatted to work with multiple locations
#
#
#

# Format the location of the log file
def interpret_location(source):
    # Get the value of $UUFSCELL
    location = subprocess.Popen("echo $UUFSCELL", shell = True, stdout = subprocess.PIPE).stdout.read()
    # Replace any instances of $UUFSCELL found in the "location" variable
    path = source.replace("$UUFSCELL", location.strip())
    # Set the "location" variable to the new string
    options["location"] = path

# Allow users to execute the program more than once
def separate_input(arguments):
    global block
    global error_text
    global mod_locations
    global number_of_errors
    global real_name
    global requested

    for item in range(0, len(arguments)):
        current = arguments[item]
        try:
            # Ensure "show" is an integer
            if current.split("=")[0] == "show":
                options["show"] = current.split("=")[1]

            #
            # Modify
            #

            # Set "location"; variable $UUFSCELL processed in interpret_location()
            elif current.split("=")[0] == "location":
                context = current.split("=")[1].split(",")
                for obj in range(0, len(context)):
                    if obj == 0:
                        options["location"] += context[obj]
                    else:
                        options["location"] += "," + context[obj]
            # Set "location" if passed in short format
            elif current.split("=")[0] == "short":
                context = current.split("=")[1].split(",")
                for obj in range(0, len(context)):
                    if obj == 0:
                        options["location"] += "/uufs/" + context[obj] + "/sys/var/slurm/log/slurm.job.log"
                    else:
                        options["location"] += ",/uufs/" + context[obj] + "/sys/var/slurm/log/slurm.job.log"

            #
            #
            #

            # Avoid showing the help menu if "strict" provided
            elif current == "strict":
                use_strict = 1
            # Allow real names to be searched
            elif current == "realname":
                real_name = 1
            # Set node list (don't format yet; done line-by-line)
            elif current.split("=")[0] == "node":
                options["node"] = current.split("=")[1]
            # Set the user
            elif current.split("=")[0] == "user":
                options["user"] = current.split("=")[1]
            # Set the group
            elif current.split("=")[0] == "group":
                options["group"] = current.split("=")[1]
            # Set the partition
            elif current.split("=")[0] == "partition":
                options["partition"] = current.split("=")[1]
            # Set the state
            elif current.split("=")[0] == "state":
                options["state"] = current.split("=")[1]
            # Set the time limit
            elif current.split("=")[0] == "timelimit":
                options["timelimit"] = current.split("=")[1]
            # Set the run-time
            elif current.split("=")[0] == "runtime":
                options["runtime"] = current.split("=")[1]
            # Set the time percentage
            elif current.split("=")[0] == "timepercentage":
                options["timepercentage"] = current.split("=")[1]
            # Set the node number
            elif current.split("=")[0] == "nnode":
                options["nnode"] = current.split("=")[1]
            # Set the processes
            elif current.split("=")[0] == "nprocess":
                options["nprocess"] = current.split("=")[1]
            # Set the job ID
            elif current.split("=")[0] == "job":
                if len(current.split("=")) > 2:
                    build = ""
                    for text in range(1, len(current.split("="))):
                        build += current.split("=")[text] + "="
                    build = build[:len(build) - 1]
                    options["job"] = build
                else:
                    options["job"] = current.split("=")[1]
            # Set the display
            elif current.split("=")[0] == "display":
                options["display"] = current.split("=")[1]
            # If the variable cannot be found in the "options" dictionary
            else:
                number_of_errors += 1
                error_text += "Block " + str(block) + ": Did not recognize the variable \"" + current.split("=")[0] + "\"; was it entered correctly?\n"
        except:
            number_of_errors += 1
            error_text += "Block " + str(block) + ": Failed to update variable \"" + current.split("=")[0] + "\"; was it set correctly?\n"
    # Get the number of requested items
    requested = 0
    correct = []
    results = []
    # Set "requested" with the number of items the user has entered
    require = ["user", "node", "group", "partition", "job", "state", "runtime", "timelimit", "timepercentage", "nprocess", "nnode"]
    for name in require:
        if options[name] != False:
            requested += 1

    # Formatting shown only in "simple" display mode
    if options["display"] == "simple":
        arg_list = "Add parameters: "
        for arg in arguments:
            arg_list += "\"" + arg + "\" "
        print(arg_list + "\n")

    #
    #
    #
    # "interpret_location" only works with a string; may need to format to a list (split at ",") and iterate over each element
    #
    #
    #

    locations = options["location"].split(",")
    for loc in range(0, len(locations)):
        if locations[loc] == "":
            locations[loc] = "/uufs/$UUFSCELL/sys/var/slurm/log/slurm.job.log"
        print(locations[loc])
        interpret_location(locations[loc])
        if len(locations) != 1 and loc != len(locations) - 1:
            mod_locations = 1
        else:
            mod_locations = 0
        run()

# Convert user input to information in "options" dictionary
def interpret_input():
    global block
    global error_text
    global number_of_errors
    last_value = 1
    going = []
    for value in range(1, len(sys.argv)):
        # Split input at "+" symbol
        if sys.argv[value] == "+":
            block += 1
            separate_input(going)
            # Reset "going" to allow new items to be added without repeats
            going = []
        # Split input if the end of the line is reached
        elif value == len(sys.argv) - 1:
            # Increase the number of blocks that have been found
            block += 1
            going.append(sys.argv[value])
            separate_input(going)
        # Append all other arguments
        else:
            going.append(sys.argv[value])

# Begin organizing information and run the program
def call_run():
    interpret_input()
    # Show error output only if display is "simple"
    if number_of_errors > 0 and (options["display"] == "simple"):
        was_were = "was" if number_of_errors == 1 else "were"
        error_errors = "error" if number_of_errors == 1 else "errors"
        print(str(number_of_errors) + " non-critical " + error_errors + " " + was_were + " encountered.\n" + error_text)
    # No errors
    elif options["display"] == "simple":
        print("No known errors were encountered during execution.\n")





# ------------------------------------------ #
# Input collection and function organization #
# ------------------------------------------ #

# Interpret input
try:
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and (sys.argv[1] == "help" or sys.argv[1] == "h")):
        # Prevent the help menu from being displayed if "strict" is entered
        if use_strict == 1:
            # Execute the program
            call_run()
        else:
            # Display help menu if requested (or when no arguments are given); in separate print statements to allow output to be "piped"
            print("To override the help menu, run \"" + sys.argv[0] + " strict\"")
            print(sys.argv[0] + " help\n-----\n")
            print("Command usage:\n  Most arguments are passed in the format argument=value.\n  To use characters that must be escaped (including spaces and ampersands), use argument=\"value\" or \"argument=value.\"\n  Stand-alone arguments are used in the format \"argument.\"\n  Examples:\n    show=4 short=ember.arches node=\"5 or 20\"\n    show=\"3\" short=\"lonepeak.peaks\" node=\"5-20 or 30\" realname\n    job=\">=123456\" display=neat timepercentage=\">=50\" \"realname\"\n-----\n")
            print("Block system:\n  \"Blocks\" can be executed with different parameters.\n  Arguments do not reset for each block; values passed in the first block remain the same in later blocks unless changed explicitly.\n  Usage:\n    argument argument argument + argument + argument\n  Examples:\n    show=5 display=neat short=kingspeak.peaks + short=lonepeak.peaks + short=ember.arches\n      Show 5 results from each location given (arguments add from left to right)\n    show=1 display=simple + display=format + display=neat\n      Show the most recent job in three different display modes (the job will be the same in each)\n-----\n")
            print("Options available through arguments:\nshow\n  The number of results to display.\n  Options:\n    integer (e.g. 1, 5, 20)\n    \"all\": Show all matching results.\n")
            print("location\n  The location of the log file (as an absolute path).\n  Options:\n    string (e.g. /path/to/file.log)\n")
            print("short\n  The short-hand location of the log file.\n  Options:\n    string (e.g. lonepeak.peaks)\n    \"$UUFSCELL\" (default): Use the current cluster.\n")
            print("user\n  The user ID to search.\n  Options:\n    string (e.g. u0123456)\n    logical (e.g. \"u0123456 or u0000000\")\n")
            print("node\n  The nodes to search.\n  Options:\n    string (e.g. kp[001-005], kp1-kp5, [1-5], \"1,5\")\n    integer (e.g. 5)\n    logical (e.g. \"not 301\", \"not kp[001-005]\")\n")
            print("group\n  The group to which the user belongs.\n  Options:\n    string (e.g. abc, xyz)\n    logical (e.g. \"abc or xyz\")\n")
            print("job\n  The job number to search.\n  Options:\n    integer (e.g. 012345)\n    logical (e.g. \"12345 or 11111\", \">=500\")\n")
            print("partition\n  The partition on which the job ran.\n  Options:\n    string (e.g. kingspeak-guest)\n    logical (e.g. \"kingpeak-guest or kingspeak\")\n")
            print("state\n  The state of the job.\n  Options:\n    string (e.g. cancelled, completed)\n    logical (e.g. \"cancelled or completed\")\n")
            print("runtime\n  The run-time of the program, in minutes.\n  Options:\n    integer (e.g. 60, 0.5)\n    logical (e.g. \"5 or 10\", \"<10\")\n")
            print("timelimit\n  The time limit specified by the user, in minutes.\n  Options:\n    integer (e.g. 15, 600)\n    logical (e.g. \"10 or 60\", \">=40\")\n")
            print("timepercentage\n  The percentage of the time limit that was used by the program.\n  Options:\n    integer (e.g. 50)\n    logical (e.g. \">=40\", \"5 or 10\")\n")
            print("nnode\n  The number of nodes that were used by the job.\n  Options:\n    integer (e.g. 0, 1, 50)\n    logical (e.g. \">20\", \"10 or 20\")\n")
            print("nprocess\n  The number of process that were used by the job.\n  Options:\n    integer (e.g. 10, 20, 50)\n    logical (e.g. \"40 or 500\", \"<=50\")\n")
            print("strict\n  Stand-alone; avoid showing the help menu with no other arguments.\n")
            print("realname\n  Stand-alone; try to find the real name of users (not shown in \"display=format\").\n")
            print("display\n  The display options to be used by the program.\n  Options:\n    \"simple\" (default): Show information in a human-readable manner.\n    \"neat\": Format all information for parsing.\n    \"format\": Format the Slurm line for parsing.")
    else:
        # Execute the main body of the program if no help is required
        call_run()
except KeyboardInterrupt:
    # Allow users to cancel the execution of the program from any point by encompassing all program calls in the same "try" statement
    sys.exit("\nProgram aborted by user at " + str(datetime.datetime.now()).split(".")[0] + ".")
