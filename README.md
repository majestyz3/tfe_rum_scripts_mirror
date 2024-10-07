# TFE RUM Scripts
This repo contains scripts that can count RUM and aggregrate data for TFE instances. These scripts use the API and count using each workspaces current state version. 

The repo also contains two SQL queries. One for gathering the total RUM for a TFE organization and one for counting the total number of worksapces. These queries must be run against the TFE database. 

## Usage

Below usage instructions for Python and Bash scripts, for the rails console version check [this README.md](tfectl_rails_console/README.md).

### Python Usage

**Note**: The Python script is multi-threaded, making it much faster than the bash script. Both scripts work, but if an organization has over 1k workspaces the Python script should be used to avoid long runtimes. The bash script takes roughly 30 minutes to run for 2k workspaces. 
```
python3 gather_billable_rum.py [-h] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-a ADDR] [-v] [-p PATH] [-f FILE] [-o ORGANIZATON] [--csv CSV]

Script to output basic Workspace Info (workspace ID, name, version, # resources) as well as an accurate RUM count.

options:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level (default: ERROR)
  -a ADDR, --addr ADDR  URL for your TFE Server (default: 'https://app.terraform.io')
  -o ORGANIZATION, --organization ORGANIZATION
                        Limit results to one organization. Default: all organizations your token can access.
  -v, --verbose         Verbose will print details for every organization, otherwise only a summary table will appear.
  -p PATH, --path PATH  Path where state files are stored.
  -f FILE, --file FILE  Output file for results   (*** COMING SOON ***)
  --csv CSV             Output in CSV format      (*** COMING SOON ***)
```
#### Install dependencies (Python only)
```$ pip install -r requirements.txt```


#### Optional Environment Variables:
**TF_ADDR**: Address of TFE Server.  If not set, assumes TFC ("https://app.terraform.io"), DO NOT add api/v2 path to the address.


**TF_TOKEN**: valid TFC Token, precendence is:
1. TF_TOKEN
2. ~/.terraform.d/credentials.tfrc.json 
3. User prompt

_TF_ORG_: Organization Name


Example usage) 
```
TF_TOKEN=asdfasdfuxuxuxuxu  TF_ADDR=https://my.domain.io python3 gather_billable_rum.py   
```


### Bash Usage
The bash script requires [jq](https://jqlang.github.io/jq/) and cURL to work correctly. 
``` 
./gather_billable_rum.sh <API_URL> <ORG_NAME>

A "TOKEN" env variable should be set with a valid API token for the organization that is being accessed. 

API_URL - the base url of the API to pull data from. ex) app.terraform.io

ORG_NAME - the name of the organization to pull data from

example) TOKEN=aaaxxxfffkkk ./gather_billable_rum.sh app.terraform.io example_org
```
### Simpler Bash Usage

This script will use the TFE API to gather data about billable RUM for an
Organization. The output is in tabular form, meant for human consumption.

This script will use the appropriate API token in the credentials.tfrc.json
file for the invoking user. A "TOKEN" env variable can optionally be set
with a valid API token for the Organization that is being accessed. 

API_URL - the base url of the API to pull data from. ex) app.terraform.io

ORG_NAME - the name of the TFE/TFC Organization to pull data from

Example usage:
  ```
  ./gather_billable_rum-simple.sh app.terraform.io example_org
  ```

  OR

  ```
  export TOKEN=aaaxxxfffkkk
  ./gather_billable_rum-simple.sh app.terraform.io example_org
  ```


### SQL Script Usage
The SQL script can be ran using any SQL agent that has permission to read from the TFE database. You must ensure the correct database is selected (`tfe`) and the database user running the query has adequate permissions. 

The `gather_billable_rum.sql` file contains two queries. One query to count RUM and one to count the total number of workspaces for an organization. These queries should be pasted into the SQL client separatly (or one of the queries commented out) as they are meant to be run as two distinct queries. 


## Example Output for the Bash Script
```
{
  "organization_name": "test-org",
  "organization_total_resources": 12949,
  "organization_managed_resources": 12726,
  "organization_data_resources": 223,
  "organization_billable_rum": 12724,
  "workspace_total": 2,
  "workspaces": [
    {
      "name": "test2-workspace",
      "total_resources": 12,
      "managed_resources": 12,
      "billable_resources": 10,
      "data_resources": 0,
      "terraform_version": "1.5.6",
      "resource_summary": {
        "providers": {
          "fakewebservices_database": 1,
          "fakewebservices_load_balancer": 1,
          "fakewebservices_server": 7,
          "fakewebservices_vpc": 1,
          "null_resource": 2
        },
        "provider_types": {
          "provider[\"registry.terraform.io/hashicorp/fakewebservices\"]": 10,
          "provider[\"registry.terraform.io/hashicorp/null\"]": 2
        }
      }
    },
    {
      "name": "test",
      "total_resources": 12937,
      "managed_resources": 12714,
      "billable_resources": 12714,
      "data_resources": 223,
      "terraform_version": "1.4.2",
      "resource_summary": {
        "providers": {
          "random_password": 1,
          "snowflake_account_grant": 1,
          "snowflake_database": 8,
          "snowflake_managed_account": 1,
          "snowflake_network_policy": 19,
          "snowflake_network_policy_attachment": 19,
          "snowflake_oauth_integration": 2,
          "snowflake_resource_monitor": 1,
          "snowflake_role": 155,
          "snowflake_role_grants": 9,
          "snowflake_saml_integration": 1,
          "snowflake_scim_integration": 1,
          "snowflake_warehouse": 48,
          "snowflake_user": 7,
          "aws_secretsmanager_secret": 1,
          "aws_secretsmanager_secret_version": 1,
          "data.snowflake_schemas": 3,
          "data.snowflake_tables": 220,
          "snowflake_database_grant": 3,
          "snowflake_schema_grant": 220,
          "snowflake_share": 3,
          "snowflake_table_grant": 12213
        },
        "provider_types": {
          "provider[\"registry.terraform.io/hashicorp/random\"]": 1,
          "provider[\"registry.terraform.io/snowflake-labs/snowflake\"]": 12670,
          "provider[\"registry.terraform.io/snowflake-labs/snowflake\"].snowflake_sysadmin": 56,
          "provider[\"registry.terraform.io/snowflake-labs/snowflake\"].snowflake_securityadmin": 208,
          "provider[\"registry.terraform.io/hashicorp/aws\"]": 2
        }
      }
    }
  ]
}

```
## Example Output for the Python Script
The Python script additionally collates workspaces by project, with a billable resource count per project.
```
{
  "organization_name": "philbrook",
  "workspace_total": 10,
  "project_total": 4,
  "projects": [
    {
      "name": "acme-corp",
      "id": "prj-LLTLTUteEbAX7XXx",
      "billable_resources": 0,
      "workspaces": []
    },
    {
      "name": "Default Project",
      "id": "prj-TLtrJ3oxMSWdcmfN",
      "billable_resources": 21,
      "workspaces": [
        {
          "id": "ws-zQim4j3kZoUzw26f",
          "name": "tfe-scratch",
          "terraform_version": "1.8.2",
          "project_id": "prj-TLtrJ3oxMSWdcmfN",
          "billable_resources": 15,
          "data_resources": 2,
          "managed_resources": 15,
          "total_resources": 17,
          "resource_summary": {
            "providers": {
              "data.aws_ami": 1,
              "data.aws_iam_openid_connect_provider": 1,
              "aws_iam_policy": 1,
              "aws_iam_role": 1,
              "aws_iam_role_policy_attachment": 1,
              "aws_instance": 1,
              "aws_key_pair": 1,
              "aws_route53_record": 1,
              "aws_route53_zone": 1,
              "aws_security_group": 1,
              "aws_vpc_security_group_egress_rule": 1,
              "aws_vpc_security_group_ingress_rule": 3,
              "tfe_variable": 2,
              "tfe_variable_set": 1
            },
            "provider_types": {
              "provider[\"registry.terraform.io/hashicorp/aws\"]": 14,
              "provider[\"registry.terraform.io/hashicorp/tfe\"]": 3
            }
          }
        },
        {
          "id": "ws-GH6Umwk8MEujANkf",
          "name": "test-cli",
          "terraform_version": "1.8.5",
          "project_id": "prj-TLtrJ3oxMSWdcmfN",
          "billable_resources": 2,
          "data_resources": 3,
          "managed_resources": 2,
          "total_resources": 5,
          "resource_summary": {
            "providers": {
              "data.aws_caller_identity": 1,
              "data.aws_partition": 1,
              "data.aws_region": 1,
              "aws_s3_bucket": 1,
              "aws_s3_bucket_public_access_block": 1
            },
            "provider_types": {
              "provider[\"registry.terraform.io/hashicorp/aws\"]": 5
            }
          }
        },
        {
          "id": "ws-cV7C8KwsSavw11j2",
          "name": "test-api",
          "terraform_version": "1.8.5",
          "project_id": "prj-TLtrJ3oxMSWdcmfN",
          "billable_resources": 2,
          "data_resources": 3,
          "managed_resources": 2,
          "total_resources": 5,
          "resource_summary": {
            "providers": {
              "data.aws_caller_identity": 1,
              "data.aws_partition": 1,
              "data.aws_region": 1,
              "aws_s3_bucket": 1,
              "aws_s3_bucket_public_access_block": 1
            },
            "provider_types": {
              "provider[\"registry.terraform.io/hashicorp/aws\"]": 5
            }
          }
        },
        {
          "id": "ws-2X86VRhGrgPfxQ2H",
          "name": "tfe-scratch-subpath",
          "terraform_version": "1.8.5",
          "project_id": "prj-TLtrJ3oxMSWdcmfN",
          "billable_resources": 0,
          "data_resources": 1,
          "managed_resources": 0,
          "total_resources": 1,
          "resource_summary": {
            "providers": {
              "terraform_data": 1
            },
            "provider_types": {
              "provider[\"terraform.io/builtin/terraform\"]": 1
            }
          }
        },
        {
          "id": "ws-VxWmvDoQZ21ab4hh",
          "name": "test-storage",
          "terraform_version": "1.8.5",
          "project_id": "prj-TLtrJ3oxMSWdcmfN",
          "billable_resources": 2,
          "data_resources": 3,
          "managed_resources": 2,
          "total_resources": 5,
          "resource_summary": {
            "providers": {
              "data.aws_caller_identity": 1,
              "data.aws_partition": 1,
              "data.aws_region": 1,
              "aws_s3_bucket": 1,
              "aws_s3_bucket_public_access_block": 1
            },
            "provider_types": {
              "provider[\"registry.terraform.io/hashicorp/aws\"]": 5
            }
          }
        }
      ]
    },
    {
      "name": "dynamic-creds-bootstrap",
      "id": "prj-jZxvbi2onJnHMPeu",
      "billable_resources": 7,
      "workspaces": [
        {
          "id": "ws-n73pP2AAuzfGFMsA",
          "name": "dynamic-creds-aws-bootstrap",
          "terraform_version": "~>1.8.0",
          "project_id": "prj-jZxvbi2onJnHMPeu",
          "billable_resources": 7,
          "data_resources": 2,
          "managed_resources": 7,
          "total_resources": 9,
          "resource_summary": {
            "providers": {
              "data.tfe_project": 1,
              "data.tls_certificate": 1,
              "aws_iam_openid_connect_provider": 1,
              "aws_iam_policy": 1,
              "aws_iam_role": 1,
              "aws_iam_role_policy_attachment": 1,
              "tfe_variable": 2,
              "tfe_workspace": 1
            },
            "provider_types": {
              "provider[\"registry.terraform.io/hashicorp/tfe\"]": 4,
              "provider[\"registry.terraform.io/hashicorp/tls\"]": 1,
              "provider[\"registry.terraform.io/hashicorp/aws\"]": 4
            }
          }
        }
      ]
    },
    {
      "name": "lambda-fun",
      "id": "prj-fH8F6t8pcX2zYQGY",
      "billable_resources": 97,
      "workspaces": [
        {
          "id": "ws-v5in4HTBM4TrjEUQ",
          "name": "test-run-task-2",
          "terraform_version": "1.9.5",
          "project_id": "prj-fH8F6t8pcX2zYQGY",
          "billable_resources": 20,
          "data_resources": 6,
          "managed_resources": 20,
          "total_resources": 26,
          "resource_summary": {
            "providers": {
              "data.aws_iam_policy_document": 1,
              "data.tfe_organization_run_task": 1,
              "data.tfe_workspace": 1,
              "aws_api_gateway_deployment": 1,
              "aws_api_gateway_integration": 1,
              "aws_api_gateway_method": 1,
              "aws_api_gateway_method_settings": 1,
              "aws_api_gateway_resource": 1,
              "aws_api_gateway_rest_api": 1,
              "aws_api_gateway_stage": 1,
              "aws_cloudwatch_log_group": 2,
              "aws_iam_role": 1,
              "aws_lambda_function": 1,
              "aws_lambda_permission": 1,
              "aws_s3_object": 1,
              "github_actions_variable": 2,
              "github_repository": 1,
              "tfe_workspace_run": 1,
              "tfe_workspace_run_task": 1,
              "data.aws_caller_identity": 1,
              "data.aws_partition": 1,
              "data.aws_region": 1,
              "aws_s3_bucket": 1,
              "aws_s3_bucket_public_access_block": 1
            },
            "provider_types": {
              "provider[\"registry.terraform.io/hashicorp/aws\"]": 19,
              "provider[\"registry.terraform.io/hashicorp/tfe\"]": 4,
              "provider[\"registry.terraform.io/integrations/github\"]": 3
            }
          }
        },
        {
          "id": "ws-7P2KTFCWWKcQz8TA",
          "name": "lambda-cli",
          "terraform_version": "1.9.3",
          "project_id": "prj-fH8F6t8pcX2zYQGY",
          "billable_resources": 15,
          "data_resources": 4,
          "managed_resources": 15,
          "total_resources": 19,
          "resource_summary": {
            "providers": {
              "data.aws_iam_policy_document": 1,
              "aws_api_gateway_deployment": 1,
              "aws_api_gateway_integration": 1,
              "aws_api_gateway_method": 1,
              "aws_api_gateway_method_settings": 1,
              "aws_api_gateway_resource": 1,
              "aws_api_gateway_rest_api": 1,
              "aws_api_gateway_stage": 1,
              "aws_cloudwatch_log_group": 2,
              "aws_iam_role": 1,
              "aws_lambda_function": 1,
              "aws_lambda_permission": 1,
              "aws_s3_object": 1,
              "data.aws_caller_identity": 1,
              "data.aws_partition": 1,
              "data.aws_region": 1,
              "aws_s3_bucket": 1,
              "aws_s3_bucket_public_access_block": 1
            },
            "provider_types": {
              "module.function.provider[\"registry.terraform.io/hashicorp/aws\"]": 19
            }
          }
        },
        {
          "id": "ws-gLm5jA7qXeY6PddV",
          "name": "lambda-playground",
          "terraform_version": "1.8.5",
          "project_id": "prj-fH8F6t8pcX2zYQGY",
          "billable_resources": 44,
          "data_resources": 11,
          "managed_resources": 44,
          "total_resources": 55,
          "resource_summary": {
            "providers": {
              "data.archive_file": 1,
              "data.aws_iam_policy_document": 3,
              "data.tls_certificate": 1,
              "aws_api_gateway_account": 1,
              "aws_api_gateway_deployment": 2,
              "aws_api_gateway_integration": 3,
              "aws_api_gateway_method": 3,
              "aws_api_gateway_method_settings": 2,
              "aws_api_gateway_resource": 3,
              "aws_api_gateway_rest_api": 2,
              "aws_api_gateway_stage": 2,
              "aws_cloudwatch_log_group": 5,
              "aws_iam_openid_connect_provider": 1,
              "aws_iam_policy": 1,
              "aws_iam_role": 4,
              "aws_iam_role_policy_attachment": 1,
              "aws_lambda_function": 3,
              "aws_lambda_permission": 3,
              "aws_s3_object": 1,
              "github_actions_variable": 2,
              "github_repository": 1,
              "data.aws_caller_identity": 2,
              "data.aws_partition": 2,
              "data.aws_region": 2,
              "aws_s3_bucket": 2,
              "aws_s3_bucket_public_access_block": 2
            },
            "provider_types": {
              "provider[\"registry.terraform.io/hashicorp/archive\"]": 1,
              "provider[\"registry.terraform.io/hashicorp/aws\"]": 31,
              "provider[\"registry.terraform.io/hashicorp/tls\"]": 1,
              "module.function.provider[\"registry.terraform.io/hashicorp/aws\"]": 19,
              "module.function.provider[\"registry.terraform.io/integrations/github\"]": 3
            }
          }
        },
        {
          "id": "ws-HDxijx6PcgV74yxh",
          "name": "lambda-fib",
          "terraform_version": "1.9.4",
          "project_id": "prj-fH8F6t8pcX2zYQGY",
          "billable_resources": 18,
          "data_resources": 4,
          "managed_resources": 18,
          "total_resources": 22,
          "resource_summary": {
            "providers": {
              "data.aws_iam_policy_document": 1,
              "aws_api_gateway_deployment": 1,
              "aws_api_gateway_integration": 1,
              "aws_api_gateway_method": 1,
              "aws_api_gateway_method_settings": 1,
              "aws_api_gateway_resource": 1,
              "aws_api_gateway_rest_api": 1,
              "aws_api_gateway_stage": 1,
              "aws_cloudwatch_log_group": 2,
              "aws_iam_role": 1,
              "aws_lambda_function": 1,
              "aws_lambda_permission": 1,
              "aws_s3_object": 1,
              "github_actions_variable": 2,
              "github_repository": 1,
              "data.aws_caller_identity": 1,
              "data.aws_partition": 1,
              "data.aws_region": 1,
              "aws_s3_bucket": 1,
              "aws_s3_bucket_public_access_block": 1
            },
            "provider_types": {
              "provider[\"registry.terraform.io/hashicorp/aws\"]": 19,
              "provider[\"registry.terraform.io/integrations/github\"]": 3
            }
          }
        }
      ]
    }
  ],
  "organization_total_resources": 164,
  "organization_managed_resources": 125,
  "organization_data_resources": 39,
  "organization_billable_rum": 125
}
```
