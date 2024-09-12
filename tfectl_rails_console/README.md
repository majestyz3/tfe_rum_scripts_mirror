# TFE RUM Scripts - internal console

Scripts that can count RUM and aggregate data for TFE instances using ruby/rails code, leveraging TFE's internal console (see [documentation](https://developer.hashicorp.com/terraform/enterprise/deploy/reference/cli#connect-to-the-internal-rails-console)).

## Usage

The ruby script works in any HCP Terraform rails console environment (even TFC) by running:

```
[1] [atlas]> load('gather_billable_rum.rb')
[1] [atlas]> GatherBillableRum.new.call

[
  {
    "grand_total": {
      "billable_resources": 0,
      "managed_resources": 0,
      "data_resources": 0,
      "total_resources": 0
    }
  },
  {
    "cost_optimization_total": {
      "total_idle_billable_workspaces": 0,
      "total_zero_billable_workspaces": 0,
      "total_non_zero_billable_workspaces": 0
    }
  }
]
```

Another script is also provided as a "packaged" version that facilitates execution in TFE environments by loading the ruby script and executing within a `tfectl support console` session. That script needs to be built first:

```
$ ./pkg.sh
Script written successfully to dist/gather_billable_rum-rb.sh
```

That will generate another script in the dist directory, and is the one to be shared to be executed in TFE's environment:

**Note**: This script is intentionally ommitting logs, only printing the json output data

```
# copy the script to the host where TFE is running (example with gcloud):
4 gcloud compute scp --zone "us-east1-c" --tunnel-through-iap --project "$PROJECT" dist/gather_billable_rum-rb.sh "$INSTANCE:gather_billable_rum-rb.sh"

# ssh to the instance
$ gcloud compute ssh --zone "us-east1-c" --tunnel-through-iap --project "$PROJECT"

# execute the script
$ sudo ./gather_billable_rum-rb.sh
[
  {
    "grand_total": {
      "billable_resources": 0,
      "managed_resources": 0,
      "data_resources": 0,
      "total_resources": 0
    }
  },
  {
    "cost_optimization_total": {
      "total_idle_billable_workspaces": 0,
      "total_zero_billable_workspaces": 0,
      "total_non_zero_billable_workspaces": 0
    }
  }
]
```