# Imports
import argparse
import json
import logging
import os
import time
import util

##
## Function Set-up Logging
##
def setup_logging(log_level):
    log_format = "%(levelname)s:%(asctime)s %(message)s"
    logging.basicConfig(format=log_format, level=log_level)

##
## Function Parse command line args
##
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Script to output basic CE state file Info (version, # resources) as well as an accurate RUM count."
    )
    # group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "-l",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Set the logging level (default: ERROR)",
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help="Verbose will print details for every organization, otherwise only a summary table will appear.",
        action='store_true'
    )
    parser.add_argument(
        '-p',
        '--path',
        help="Path where state files are stored.",
        required=True
    )
    return parser.parse_args()


##
## print_summary: Prints the summary report 
##
def print_summary(rum_sum):
    # Initialize variables for subtotal and grand total
    grand_total = {'rum': 0, 'null_rs': 0, 'data_rs': 0, 'total': 0}

    # Define the column headers with right-justification
    headers = ["Name", "Version", "Billable RUM", "Data RS", "Null RS", "Total"]
    header_format = "{:<40}{:<10}{:>15}{:>10}{:>10}{:>10}"
    print(header_format.format(*headers))

    for state in rum_sum:
        # Truncate the name if it exceeds 40 characters
        name = state['name']
        if len(name) > 39:
            name = name[:36] + "..."

        # Define the row values with right-justification
        row_values = [
            state['name'], state['terraform-version'],
            state['resources']['rum'],
            state['resources']['data_rs'], state['resources']['null_rs'], state['resources']['total']
        ]
        row_format = "{:<40}{:<10}{:>15}{:>10}{:>10}{:>10}"
        print(row_format.format(*row_values))

        # Accumulate grand total
        grand_total['rum'] += state['resources']['rum']
        grand_total['null_rs'] += state['resources']['null_rs']
        grand_total['data_rs'] += state['resources']['data_rs']
        grand_total['total'] += state['resources']['total']

    # Print grand total row
    print(f"\nGrand Total:")
    print(row_format.format('', '', grand_total['rum'], grand_total['data_rs'], grand_total['null_rs'], grand_total['total']))



##
## process_oss: User specified a path for statefiles
##
def process_oss(path):
    logging.info(f"Processing OSS")
    rum_sum = []  # rum_sum a list of organization results
    statefiles = []  

    # Convert each state file into a json object
    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.endswith('.tfstate'):
                file_path = os.path.join(root,filename)
                print (f"Processing file: {file_path}")
                with open(file_path) as file:
                    json_data = json.load(file)
                    json_data['id'] = filename
                    statefiles.append(json_data)

    for state in statefiles:
        # logging.info(f"Processing ws: {ws['id']}")
        print(f"Processing statefile: {state['id']}")
        state_sum = {}
        state_sum['name'] = state['id']
        state_sum['terraform-version'] = state['terraform_version']
        resources = state['resources']
        rum = 0
        null_rs = 0
        data_rs = 0
        for rs in resources:
            category = util.billable_categorization(rs)
            instances = len(rs['instances'])
            if category == "null":
                null_rs += instances
            elif category == "data":
                data_rs += instances
            elif category == "billable":
                rum += instances
            else:
                logging.error(f"Unknown category {category} for resource {rs['type']}")
        state_sum['resources'] = {'rum': rum , 'null_rs':null_rs, 'data_rs': data_rs, 'total':rum+null_rs+data_rs}
        rum_sum.append(state_sum)
    return rum_sum

##########################################
## MAIN
##########################################
start_time = time.perf_counter()

# Parse command line arguments
args = parse_arguments()
verbose = args.verbose
setup_logging(args.log_level)

path = args.path
if path != None:
    rum_sum = process_oss(args.path)
else:
    logging.error("No path specified, exiting.")
    exit(1)

print_summary(rum_sum)

end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time:.3f} seconds")
