def billable_categorization(resource):
    if resource["mode"] == "managed":
        if resource["type"] not in ["terraform_data", "null_resource"]:
            return "billable"
        else:
            return "null"
    else:
        return "data"
