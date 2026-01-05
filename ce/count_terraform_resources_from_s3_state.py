import boto3
import json
import util

# Uncomment the following line to use a specific AWS profile
# boto3.setup_default_session(profile_name="aws")

s3 = boto3.resource("s3")
s3_client = boto3.client("s3")

BUCKET_NAME_FILTER_PREFIX = ""
TF_STATE_OBJ_KEY = "terraform.tfstate"

# Get a list of all buckets
all_buckets = s3.buckets.all()

# Define a variable to hold the total resource count
count = 0
# Iterate through each bucket
for bucket in all_buckets:
    if bucket.name.startswith(BUCKET_NAME_FILTER_PREFIX):
        # Gert a list of all objects in the bucket
        state_files = s3_client.list_objects_v2(Bucket=bucket.name)
        # Verify that there are files in the bucket
        if "Contents" in state_files:
            for obj in state_files["Contents"]:
                # Only match on objects that match the Terraform state file name
                if TF_STATE_OBJ_KEY in obj["Key"]:
                    this_count = 0
                    # Get the file contents
                    tf_state_file = s3_client.get_object(Bucket=bucket.name, Key=obj["Key"])
                    tf_state_file_contents = tf_state_file["Body"].read().decode("utf-8")
                    # Parse the file as JSON
                    j = json.loads(tf_state_file_contents)
                    # Run the billable RUM algorithm
                    for r in j["resources"]:
                        category = util.billable_categorization(r)
                        if category == "billable":
                            this_count += len(r["instances"])
                    # Append the results to the running counter
                    count += this_count
                    print(f"{bucket.name} {obj['Key']}: {this_count}")

print(f"Total Resources: {count}")
