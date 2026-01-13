# Count RUM from Community Edition state files stored in S3

The `count_terraform_resources_from_s3_state.py` script in this directory will search S3 buckets for Terraform Community Edition state files and
count the number of billable RUM contained therein. It uses the same algorithm for whether a
resource is billable or not as the scripts in the repo's root directory, the only difference
is that this script is suitable for a Terraform CE user who has not adopted a Terraform
commercial solution.

## Notes
* The script will search all S3 buckets to which the current credentials have access
    * There is support for limiting the buckets searched by prefix (line 11). No prefix is specified by default.
    * By default, all buckets are searched for objects named
      `terraform.tfstate`. This value is used in many code examples, but there is no default. **Ensure this value is set correctly to yield the correct results!** If the customer doesn't have a consistent convention for this key name (e.g., different `backend` blocks across the company specify different values for [this option](https://developer.hashicorp.com/terraform/language/backend/s3#key)), then customization will be required to search for different key names.
* The script requires the boto3 Python library for making AWS API calls.
* Obviously, running the script requires AWS credentials (environment variables will be the easiest).
    * Support for AWS profiles is available by uncommenting line 6

# Count RUM from Community Edition state files on disk

The `count_terraform_resources_from_file_state.py` script in this directory will search a local path for Terraform Community Edition state files and
count the number of billable RUM contained therein. It uses the same algorithm for whether a
resource is billable or not as the scripts in the repo's root directory, the only difference
is that this script is suitable for a Terraform CE user who has not adopted a Terraform
commercial solution and has access to all of their state files at a local path.

## Notes
* The script currently can search a single path for any file suffixed with `.tfstate`

## Usage
```
python3 count_terraform_resources_from_file_state.py [-h] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-v] [-p PATH]

Script to output basic state file info (filename, TF version, # resources) as well as an accurate RUM count.

options:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level (default: ERROR)
  -v, --verbose         Verbose will print details for every organization, otherwise only a summary table will appear.
  -p PATH, --path PATH  Path where state files are stored.
```

## Sample for TF CE:
```
Name                                    Version      Billable RUM   Data RS   Null RS     Total
state1.tfstate                          1.9.3                   1         0         0         1
terraform.tfstate                       1.14.0                124        35         0       159
state2.tfstate                          1.9.3                   1         0         0         1

Grand Total:
                                                              126        35         0       161
```
