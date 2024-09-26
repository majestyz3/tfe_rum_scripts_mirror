class GatherBillableRum

  def call(organizations = [], output=$stdout)
    organizations = Organization.active if organizations.empty? && TFP.enterprise? # allow gathering of billable RUM for all organizations only for TFE installations
    rum_sum = process_enterprise(organizations)
    print_summary(rum_sum, output)
  end

  private

  # 
  # process_enterprise: subroutine for TFC/TFE
  #  
  def process_enterprise(organizations)
    Rails.logger.info("Processing Enterprise")
    rum_sum = []  # rum_sum a list of organization results

    # Iterate over each org
    organizations.each do |organization|
      start_time = timestamp
      org_sum = {} # Initialize org summary
      org_sum["organization_name"] = organization.name # Set the id to org_id being processed
      org_sum["workspace_total"] = 0 # Start counting the total workspaces
      org_sum["workspaces"] = [] # Initialize the list of workspaces for the org Initialize the workspaces array

      workspaces = organization.workspaces.includes(:current_state_version)
      next if workspaces.empty?
      workspaces.each do |workspace|
        ws_sum = process_workspace(workspace)
        org_sum["workspace_total"] += 1
        org_sum["workspaces"] << ws_sum
      end
      org_sum["workspaces"].sort_by! { |ws| ws["id"] }

      # Append the org summary to RUM summary 
      rum_sum << org_sum
      elapsed_time = timestamp - start_time
      Rails.logger.debug("Processed Org: #{organization.name} in #{elapsed_time} seconds")
    end
    rum_sum
  end

  #
  # process_workspace: Helper fxn, allowing multiple workspaces to be processed in parallel
  #
  def process_workspace(workspace)
    Rails.logger.info("Processing ws: #{workspace.name}")
    ws_sum = {
      "id" => workspace.external_id,
      "name" => workspace.name,
      "terraform_version" => workspace.terraform_version,
      "active_billable_rum_count" => 0,
      "billable_resources" => 0,
      "managed_resources" => 0, 
      "data_resources" => 0, 
      "total_resources" => 0,
      "idle_billable_resources" => true,
      "zero_billable_resources" => true,
      "resource_summary" => {}
    }
    state_version = workspace.current_state_version
    return ws_sum if state_version.nil?
    ws_sum.merge!(process_resources(state_version.resources)) if state_version.supports_workspace_resources?
    ws_sum["active_billable_rum_count"] = state_version.billable_rum_count
    ws_sum["idle_billable_resources"] = state_version.billable_rum_count.nil?
    ws_sum["zero_billable_resources"] = ws_sum["active_billable_rum_count"] == 0
    ws_sum["sv_terraform_version"] = state_version.terraform_version
    ws_sum
  end

  ##
  ## process_resources: Helper Function that process the provided resources
  ##  
  def process_resources(resources)
    rum = 0
    null_rs = 0
    data_rs = 0
    total = 0
    
    type_counts = {}
    provider_type_counts = {}
  
    resources.each do |rs|
      rs['count'] = 0 if rs['count'].nil?
      type_counts[rs['type']] ||= 0
      type_counts[rs['type']] += rs['count']
  
      provider_type_counts[rs['provider']] ||= 0
      provider_type_counts[rs['provider']] += rs['count']
  
      if rs['provider'] == 'provider["registry.terraform.io/hashicorp/null"]'
        null_rs += rs['count']
      elsif rs['type'].start_with?("data") || rs['type'] == "terraform_data"
        data_rs += rs['count']
      else
        rum += rs['count']
      end
    end
    {
      'billable_resources' => rum,
      'data_resources' => data_rs,
      'managed_resources' => rum + null_rs,
      'total_resources' => rum + null_rs + data_rs,
      'resource_summary' => {
        'providers' => type_counts,
        'provider_types' => provider_type_counts
      }
    }
  end

  ##
  ## print_summary: Prints the summary report 
  ##  
  def print_summary(rum_sum, output)
    # Initialize variables for subtotal and grand total
    org_subtotal = {'billable_resources' => 0, 'managed_resources' => 0, 'data_resources' => 0, 'total_resources' => 0}
    grand_total = {'billable_resources' => 0, 'managed_resources' => 0, 'data_resources' => 0, 'total_resources' => 0}
    cost_optimization_total = {'total_idle_billable_workspaces' => 0, 'total_zero_billable_workspaces' => 0, 'total_non_zero_billable_workspaces' => 0}
  
    rum_sum.each do |org|
      org['workspaces'].each do |ws|
        # Accumulate subtotal for the organization
        org_subtotal['billable_resources'] += ws['billable_resources']
        org_subtotal['data_resources'] += ws['data_resources']
        org_subtotal['managed_resources'] += ws['managed_resources']
        org_subtotal['total_resources'] += ws['total_resources']
  
        # Accumulate grand total
        grand_total['billable_resources'] += ws['billable_resources']
        grand_total['managed_resources'] += ws['managed_resources']
        grand_total['data_resources'] += ws['data_resources']
        grand_total['total_resources'] += ws['total_resources']

        # Accumulate cost optimization totals
        cost_optimization_total['total_idle_billable_workspaces'] += 1 if ws['idle_billable_resources']
        cost_optimization_total['total_zero_billable_workspaces'] += 1 if ws['zero_billable_resources']
        cost_optimization_total['total_non_zero_billable_workspaces'] += 1 if !ws['zero_billable_resources']
      end
  
      org['organization_total_resources'] = org_subtotal['total_resources']
      org['organization_managed_resources'] = org_subtotal['managed_resources']
      org['organization_data_resources'] = org_subtotal['data_resources']
      org['organization_billable_rum'] = org_subtotal['billable_resources']
      org_subtotal = {'billable_resources' => 0, 'managed_resources' => 0, 'data_resources' => 0, 'total_resources' => 0}
    end
  
    rum_sum.unshift({grand_total: grand_total})
    rum_sum << {cost_optimization_total: cost_optimization_total}
    output.write("#{JSON.pretty_generate(rum_sum)}\n")
  end  

  def timestamp
    # https://blog.dnsimple.com/2018/03/elapsed-time-with-ruby-the-right-way/
    Process.clock_gettime(Process::CLOCK_MONOTONIC)
  end
end
