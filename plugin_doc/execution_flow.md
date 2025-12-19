
The starting flow of execution for the **AWS EC2 Instance Collector** involves a sequence of authentication, scope determination, and endpoint initialization before it begins gathering resource metadata. 

The process follows these key stages:

### **1. Authentication and Session Initialization**
The plugin first establishes a secure connection to AWS using the credentials provided in the **Secret Data** configuration. 
*   **Method Selection**: It uses either the **General Access Key Method** for single accounts or the **Cross-Account Assume Role Method** for multi-account environments.
*   **Identity Verification**: The collector utilizes the **Boto3 library** to call the **`get_caller_identity`** or **`assume_role`** APIs to verify its permissions and establish a valid session.

### **2. Regional Scope Discovery**
Once authenticated, the collector must determine which AWS regions are active and accessible.
*   **Dynamic Discovery**: Rather than relying on a hardcoded list, the collector calls the **`describe_regions()`** method of the AWS EC2 client.
*   **Targeting**: It specifically targets the regions returned by this call to ensure it only attempts to collect data from active regional infrastructures.

### **3. Endpoint Construction**
For every region identified in the discovery phase, the plugin builds a set of service-specific **AWS Service Endpoints**. 
*   **URL Generation**: It constructs URLs by combining the service code (e.g., `ec2`, `autoscaling`, or `elbv2`) with the discovered region code, such as `https://ec2.[region-code].amazonaws.com`.
*   **Resource Mapping**: These endpoints are used to route subsequent API requests to the correct regional data centers.

### **4. Initial Resource Discovery**
With the regional endpoints established, the collector begins the high-level "Describe" calls to gather metadata for the inventory. The initial execution flow typically starts with:
*   **`describe_instances`**: To find active EC2 resources.
*   **`describe_auto_scaling_groups`**: To map out the scaling infrastructure.
*   **`describe_load_balancers`**: To identify networking entry points.

The plugin is designed to handle large environments; for instance, version **1.3.1** introduced support for collecting more than **2,000 EC2 instances** by implementing API rate-limit handling and automatic retries.

***

To visualize this flow, imagine the collector is a **regional manager arriving for an inspection**. First, they **show their ID** (Authentication) to get through the gate. Next, they **check the building directory** (describe_regions) to see which offices are currently open. Then, they **look up the floor plan** (Endpoint Construction) for each office. Only after these steps do they finally begin **walking through the rooms** (Resource Discovery) to count the furniture and equipment.
